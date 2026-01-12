"""
OmniDev - DevOps Agent Router
Endpoints for the Smart DevOps Agent
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json

from app.services.devops_agent import devops_agent

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


class ActionRequest(BaseModel):
    action: str
    instance_id: Optional[str] = None
    bucket_name: Optional[str] = None
    ami_id: Optional[str] = None
    instance_type: Optional[str] = "t2.micro"
    name: Optional[str] = None


@router.get("/capabilities")
async def get_capabilities():
    """Get DevOps Agent capabilities and status"""
    return devops_agent.get_capabilities()


@router.post("/command")
async def process_command(request: CommandRequest):
    """
    Process a natural language DevOps command
    
    Examples:
    - "List my EC2 instances"
    - "What's the status of my infrastructure?"
    - "Show me my S3 buckets"
    - "Help me launch a new instance"
    """
    result = await devops_agent.process_command(request.command)
    return result


@router.get("/ec2/instances")
async def list_ec2_instances():
    """List all EC2 instances"""
    return devops_agent.list_ec2_instances()


@router.post("/ec2/launch")
async def launch_ec2_instance(request: ActionRequest):
    """Launch a new EC2 instance"""
    ami_id = request.ami_id or "ami-0dee22c13ea7a9a67"
    instance_type = request.instance_type or "t2.micro"
    name = request.name or "OmniDev-Instance"
    
    return devops_agent.launch_ec2_instance(ami_id, instance_type, name)


@router.post("/ec2/stop")
async def stop_ec2_instance(request: ActionRequest):
    """Stop an EC2 instance"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    return devops_agent.stop_ec2_instance(request.instance_id)


@router.post("/ec2/start")
async def start_ec2_instance(request: ActionRequest):
    """Start a stopped EC2 instance"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    return devops_agent.start_ec2_instance(request.instance_id)


@router.post("/ec2/terminate")
async def terminate_ec2_instance(request: ActionRequest):
    """Terminate an EC2 instance (destructive!)"""
    if not request.instance_id:
        raise HTTPException(status_code=400, detail="instance_id is required")
    return devops_agent.terminate_ec2_instance(request.instance_id)


@router.get("/s3/buckets")
async def list_s3_buckets():
    """List all S3 buckets"""
    return devops_agent.list_s3_buckets()


@router.get("/s3/objects/{bucket_name}")
async def list_s3_objects(bucket_name: str, prefix: str = ""):
    """List objects in an S3 bucket"""
    return devops_agent.list_s3_objects(bucket_name, prefix)


@router.websocket("/agent")
async def devops_agent_ws(websocket: WebSocket):
    """
    WebSocket endpoint for interactive DevOps Agent
    
    Send JSON: {"command": "your command"}
    Receive agent responses
    """
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
            
            # Process the command
            result = await devops_agent.process_command(command)
            
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
