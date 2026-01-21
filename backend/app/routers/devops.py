"""
OmniDev - DevOps Agent Router
Endpoints for the Smart DevOps Agent with user-configurable AWS credentials
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json
import boto3

from app.services.devops_agent import devops_agent, DevOpsAgent
from app.services.auth_service import decode_jwt, get_user_id, verify_api_key

router = APIRouter()


class CommandRequest(BaseModel):
    command: str
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = None


class ActionRequest(BaseModel):
    action: str
    instance_id: Optional[str] = None
    bucket_name: Optional[str] = None
    ami_id: Optional[str] = None
    instance_type: Optional[str] = "t2.micro"
    name: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = None


def get_agent(request) -> DevOpsAgent:
    """Get DevOps agent with user credentials if provided"""
    if hasattr(request, 'aws_access_key') and request.aws_access_key and request.aws_secret_key:
        return DevOpsAgent(
            aws_access_key=request.aws_access_key,
            aws_secret_key=request.aws_secret_key,
            aws_region=request.aws_region or "ap-south-1"
        )
    return devops_agent


@router.get("/capabilities")
async def get_capabilities():
    """Get DevOps Agent capabilities and status"""
    caps = devops_agent.get_capabilities()
    caps["user_credentials_supported"] = True
    return caps


@router.post("/command")
async def process_command(request: CommandRequest):
    """
    Process a natural language DevOps command
    
    Examples:
    - "List my EC2 instances"
    - "What's the status of my infrastructure?"
    - "Show me my S3 buckets"
    - "Help me launch a new instance"
    
    Optionally provide aws_access_key, aws_secret_key, aws_region to use your own credentials.
    """
    agent = get_agent(request)
    result = await agent.process_command(request.command)
    return result


@router.get("/ec2/instances")
async def list_ec2_instances():
    """List all EC2 instances"""
    return devops_agent.list_ec2_instances()


@router.post("/ec2/instances")
async def list_ec2_instances_with_creds(request: ActionRequest):
    """List all EC2 instances with optional user credentials"""
    agent = get_agent(request)
    return agent.list_ec2_instances()


@router.post("/ec2/launch")
async def launch_ec2_instance(request: ActionRequest):
    """Launch a new EC2 instance"""
    agent = get_agent(request)
    ami_id = request.ami_id or "ami-0dee22c13ea7a9a67"
    instance_type = request.instance_type or "t2.micro"
    name = request.name or "OmniDev-Instance"
    
    return agent.launch_ec2_instance(ami_id, instance_type, name)


@router.post("/ec2/stop")
async def stop_ec2_instance(request: ActionRequest):
    """Stop an EC2 instance"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    agent = get_agent(request)
    return agent.stop_ec2_instance(request.instance_id)


@router.post("/ec2/start")
async def start_ec2_instance(request: ActionRequest):
    """Start a stopped EC2 instance"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    agent = get_agent(request)
    return agent.start_ec2_instance(request.instance_id)


@router.post("/ec2/terminate")
async def terminate_ec2_instance(request: ActionRequest):
    """Terminate an EC2 instance (destructive!)"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    agent = get_agent(request)
    return agent.terminate_ec2_instance(request.instance_id)


@router.get("/s3/buckets")
async def list_s3_buckets():
    """List all S3 buckets"""
    return devops_agent.list_s3_buckets()


@router.post("/s3/buckets")
async def list_s3_buckets_with_creds(request: ActionRequest):
    """List all S3 buckets with optional user credentials"""
    agent = get_agent(request)
    return agent.list_s3_buckets()


@router.get("/s3/objects/{bucket_name}")
async def list_s3_objects(bucket_name: str, prefix: str = ""):
    """List objects in an S3 bucket"""
    return devops_agent.list_s3_objects(bucket_name, prefix)


@router.websocket("/agent")
async def devops_agent_ws(websocket: WebSocket):
    """
    WebSocket endpoint for interactive DevOps Agent
    
    Send JSON: {"command": "your command", "aws_access_key": "optional", "aws_secret_key": "optional", "aws_region": "optional"}
    Receive agent responses
    """
    token = websocket.query_params.get("token", "")
    api_key = websocket.query_params.get("api_key", "")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_jwt(token)
        user_id = get_user_id(payload)
        if not api_key or not verify_api_key(user_id, api_key):
            await websocket.close(code=4403)
            return
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    
    # Send welcome message
    await websocket.send_text(json.dumps({
        "type": "welcome",
        "message": "👋 DevOps Agent connected! How can I help you manage your cloud infrastructure?",
        "capabilities": devops_agent.get_capabilities()
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            command = request_data.get("command", "")
            
            # Check for user credentials
            aws_key = request_data.get("aws_access_key")
            aws_secret = request_data.get("aws_secret_key")
            aws_region = request_data.get("aws_region")
            
            if aws_key and aws_secret:
                agent = DevOpsAgent(
                    aws_access_key=aws_key,
                    aws_secret_key=aws_secret,
                    aws_region=aws_region or "ap-south-1"
                )
            else:
                agent = devops_agent
            
            # Process the command
            result = await agent.process_command(command)
            
            await websocket.send_text(json.dumps({
                "type": "response",
                "content": result.get("response", ""),
                "actions": result.get("actions", []),
                "context": result.get("context", {})
            }))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": str(e)
        }))
