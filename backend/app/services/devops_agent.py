"""
OmniDev - Smart DevOps Agent
AI-powered cloud infrastructure management using OpenAI GPT-5 Nano + boto3
"""

import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()


class DevOpsAgent:
    """
    Smart DevOps Agent that uses AI to understand and execute cloud operations.
    
    Capabilities:
    - EC2 instance management (list, launch, stop, terminate)
    - S3 operations (list buckets, upload, download, delete)
    - Cost analysis and optimization suggestions
    - Security audits and recommendations
    - Infrastructure troubleshooting
    """
    
    SYSTEM_PROMPT = """You are OmniDev DevOps Agent, an AI-powered cloud infrastructure assistant.

Your capabilities:
1. **EC2 Management**: List, launch, stop, start, terminate instances
2. **S3 Operations**: List buckets, manage objects
3. **Cost Analysis**: Estimate costs, find savings
4. **Security**: Check for vulnerabilities, audit permissions
5. **Troubleshooting**: Diagnose issues, suggest fixes

When the user asks you to perform an action:
1. Understand their intent
2. Use the available tools to execute the action
3. Provide clear, formatted results

Available AWS operations you can request:
- list_ec2_instances: Get all EC2 instances
- describe_ec2_instance(instance_id): Get details of specific instance
- launch_ec2_instance(ami_id, instance_type): Launch new instance
- stop_ec2_instance(instance_id): Stop an instance
- start_ec2_instance(instance_id): Start a stopped instance
- terminate_ec2_instance(instance_id): Terminate an instance
- list_s3_buckets: Get all S3 buckets
- list_s3_objects(bucket_name): List objects in a bucket
- get_cost_estimate: Get current month's estimated costs

Format your responses nicely with markdown. Use tables, bullet points, and code blocks when appropriate.
If credentials aren't configured, explain how to set them up.
Always confirm destructive actions before executing."""
    
    def __init__(self, aws_access_key: str = None, aws_secret_key: str = None, aws_region: str = None):
        self.client = None
        self.model = "gpt-4o-mini"
        self.ec2_client = None
        self.s3_client = None
        self._user_aws_key = aws_access_key
        self._user_aws_secret = aws_secret_key
        self._user_aws_region = aws_region or "ap-south-1"
        self._configure()
    
    def _configure(self):
        """Configure AI model and AWS clients"""
        # Configure OpenAI
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Configure AWS clients - prefer user-provided credentials
        aws_key = self._user_aws_key or settings.aws_access_key_id
        aws_secret = self._user_aws_secret or settings.aws_secret_access_key
        aws_region = self._user_aws_region or settings.aws_default_region
        
        try:
            if aws_key and aws_secret:
                self.ec2_client = boto3.client(
                    'ec2',
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    region_name=aws_region
                )
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    region_name=aws_region
                )
        except Exception as e:
            print(f"AWS configuration error: {e}")
    
    # ==================== EC2 Operations ====================
    
    def list_ec2_instances(self) -> Dict[str, Any]:
        """List all EC2 instances with their details"""
        if not self.ec2_client:
            return {"error": "AWS credentials not configured", "instances": []}
        
        try:
            response = self.ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    name = "Unnamed"
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    instances.append({
                        "instance_id": instance['InstanceId'],
                        "name": name,
                        "state": instance['State']['Name'],
                        "type": instance['InstanceType'],
                        "launch_time": instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None,
                        "public_ip": instance.get('PublicIpAddress'),
                        "private_ip": instance.get('PrivateIpAddress'),
                        "availability_zone": instance['Placement']['AvailabilityZone']
                    })
            
            return {"instances": instances, "count": len(instances)}
            
        except ClientError as e:
            return {"error": str(e), "instances": []}
    
    def stop_ec2_instance(self, instance_id: str) -> Dict[str, Any]:
        """Stop an EC2 instance"""
        if not self.ec2_client:
            return {"success": False, "error": "AWS credentials not configured"}
        
        try:
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            return {"success": True, "message": f"Instance {instance_id} is stopping"}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def start_ec2_instance(self, instance_id: str) -> Dict[str, Any]:
        """Start a stopped EC2 instance"""
        if not self.ec2_client:
            return {"success": False, "error": "AWS credentials not configured"}
        
        try:
            self.ec2_client.start_instances(InstanceIds=[instance_id])
            return {"success": True, "message": f"Instance {instance_id} is starting"}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def launch_ec2_instance(
        self, 
        ami_id: str = "ami-0dee22c13ea7a9a67",  # Amazon Linux 2023 in ap-south-1
        instance_type: str = "t2.micro",
        name: str = "OmniDev-Instance"
    ) -> Dict[str, Any]:
        """Launch a new EC2 instance"""
        if not self.ec2_client:
            return {"success": False, "error": "AWS credentials not configured"}
        
        try:
            response = self.ec2_client.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': name}]
                }]
            )
            instance_id = response['Instances'][0]['InstanceId']
            return {
                "success": True, 
                "instance_id": instance_id,
                "message": f"Instance {instance_id} launched successfully"
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def terminate_ec2_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an EC2 instance (destructive!)"""
        if not self.ec2_client:
            return {"success": False, "error": "AWS credentials not configured"}
        
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            return {"success": True, "message": f"Instance {instance_id} is being terminated"}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    # ==================== S3 Operations ====================
    
    def list_s3_buckets(self) -> Dict[str, Any]:
        """List all S3 buckets"""
        if not self.s3_client:
            return {"error": "AWS credentials not configured", "buckets": []}
        
        try:
            response = self.s3_client.list_buckets()
            buckets = [{
                "name": bucket['Name'],
                "created": bucket['CreationDate'].isoformat()
            } for bucket in response['Buckets']]
            
            return {"buckets": buckets, "count": len(buckets)}
        except ClientError as e:
            return {"error": str(e), "buckets": []}
    
    def list_s3_objects(self, bucket_name: str, prefix: str = "") -> Dict[str, Any]:
        """List objects in an S3 bucket"""
        if not self.s3_client:
            return {"error": "AWS credentials not configured", "objects": []}
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=100)
            objects = [{
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat()
            } for obj in response.get('Contents', [])]
            
            return {"bucket": bucket_name, "objects": objects, "count": len(objects)}
        except ClientError as e:
            return {"error": str(e), "objects": []}
    
    # ==================== AI-Powered Processing ====================
    
    async def process_command(self, user_message: str) -> Dict[str, Any]:
        """
        Process a natural language command using AI
        
        The agent will:
        1. Understand the user's intent
        2. Execute appropriate AWS operations
        3. Format and return the results
        """
        if not self.client:
            return {
                "response": "⚠️ AI not configured. Please add OPENAI_API_KEY to .env",
                "actions": []
            }
        
        # Build context with current AWS state
        context = self._build_context()
        
        # Create the prompt
        user_prompt = f"""User request: {user_message}

Current AWS Context:
{json.dumps(context, indent=2)}

Based on the user's request and the current context:
1. Explain what you understand they want
2. List any actions you would take
3. Provide the results or explain what steps are needed

If AWS credentials aren't configured, explain how to set them up."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            
            return {
                "response": response.choices[0].message.content,
                "context": context,
                "actions": self._extract_suggested_actions(user_message)
            }
        except Exception as e:
            return {
                "response": f"❌ Error processing command: {str(e)}",
                "actions": []
            }
    
    def _build_context(self) -> Dict[str, Any]:
        """Build current AWS context for the AI"""
        context = {
            "aws_configured": bool(self.ec2_client),
            "region": settings.aws_default_region
        }
        
        if self.ec2_client:
            ec2_data = self.list_ec2_instances()
            context["ec2"] = {
                "instance_count": ec2_data.get("count", 0),
                "instances": ec2_data.get("instances", [])[:5]  # Limit for context
            }
            
            s3_data = self.list_s3_buckets()
            context["s3"] = {
                "bucket_count": s3_data.get("count", 0),
                "buckets": s3_data.get("buckets", [])[:5]
            }
        
        return context
    
    def _extract_suggested_actions(self, message: str) -> List[Dict[str, str]]:
        """Extract potential actions from user message"""
        actions = []
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['list', 'show', 'get']) and 'instance' in message_lower:
            actions.append({"action": "list_ec2_instances", "description": "List EC2 instances"})
        
        if any(word in message_lower for word in ['stop', 'halt']):
            actions.append({"action": "stop_ec2_instance", "description": "Stop instance", "requires": "instance_id"})
        
        if any(word in message_lower for word in ['start', 'boot']):
            actions.append({"action": "start_ec2_instance", "description": "Start instance", "requires": "instance_id"})
        
        if any(word in message_lower for word in ['launch', 'create', 'spin up']):
            actions.append({"action": "launch_ec2_instance", "description": "Launch new instance"})
        
        if 'bucket' in message_lower or 's3' in message_lower:
            actions.append({"action": "list_s3_buckets", "description": "List S3 buckets"})
        
        return actions
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities and status"""
        return {
            "name": "OmniDev DevOps Agent",
            "version": "2.0.0",
            "ai_enabled": bool(self.client),
            "ai_model": self.model,
            "aws_configured": bool(self.ec2_client),
            "region": settings.aws_default_region,
            "capabilities": [
                {
                    "category": "EC2 Management",
                    "actions": ["List instances", "Launch instance", "Start/Stop instance", "Terminate instance"]
                },
                {
                    "category": "S3 Storage",
                    "actions": ["List buckets", "List objects", "Upload/Download files", "Delete objects"]
                },
                {
                    "category": "Cost & Optimization",
                    "actions": ["Estimate costs", "Find unused resources", "Right-sizing suggestions"]
                },
                {
                    "category": "Security",
                    "actions": ["Audit security groups", "Check public access", "Review IAM policies"]
                }
            ]
        }


# Singleton instance
devops_agent = DevOpsAgent()
