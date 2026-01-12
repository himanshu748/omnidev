"""
OmniDev - Storage Router
Endpoints for S3 file operations
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io

from app.services.devops_agent import devops_agent
from app.config import get_settings

settings = get_settings()
router = APIRouter()


class UploadRequest(BaseModel):
    bucket_name: str
    key: str


@router.get("/buckets")
async def list_buckets():
    """List all S3 buckets"""
    return devops_agent.list_s3_buckets()


@router.get("/buckets/{bucket_name}/objects")
async def list_objects(bucket_name: str, prefix: str = ""):
    """
    List objects in an S3 bucket
    
    - **bucket_name**: Name of the S3 bucket
    - **prefix**: Optional prefix to filter objects
    """
    return devops_agent.list_s3_objects(bucket_name, prefix)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    bucket_name: str = Form(...),
    key: Optional[str] = Form(None)
):
    """
    Upload a file to S3
    
    - **file**: The file to upload
    - **bucket_name**: Target S3 bucket
    - **key**: Object key (filename if not provided)
    """
    if not devops_agent.s3_client:
        raise HTTPException(status_code=503, detail="AWS credentials not configured")
    
    try:
        # Use filename if key not provided
        object_key = key or file.filename
        
        # Read file content
        content = await file.read()
        
        # Upload to S3
        devops_agent.s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=content,
            ContentType=file.content_type
        )
        
        return {
            "success": True,
            "message": f"File uploaded successfully",
            "bucket": bucket_name,
            "key": object_key,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{bucket_name}/{key:path}")
async def download_file(bucket_name: str, key: str):
    """
    Download a file from S3
    
    - **bucket_name**: S3 bucket name
    - **key**: Object key (file path)
    """
    if not devops_agent.s3_client:
        raise HTTPException(status_code=503, detail="AWS credentials not configured")
    
    try:
        response = devops_agent.s3_client.get_object(Bucket=bucket_name, Key=key)
        
        # Get content type
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Stream the file
        return StreamingResponse(
            io.BytesIO(response['Body'].read()),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={key.split('/')[-1]}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{bucket_name}/{key:path}")
async def delete_file(bucket_name: str, key: str):
    """
    Delete a file from S3
    
    - **bucket_name**: S3 bucket name
    - **key**: Object key (file path)
    """
    if not devops_agent.s3_client:
        raise HTTPException(status_code=503, detail="AWS credentials not configured")
    
    try:
        devops_agent.s3_client.delete_object(Bucket=bucket_name, Key=key)
        
        return {
            "success": True,
            "message": f"File deleted successfully",
            "bucket": bucket_name,
            "key": key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def storage_status():
    """Check Storage service status"""
    return {
        "service": "S3 Storage",
        "provider": "AWS S3",
        "status": "configured" if devops_agent.s3_client else "not configured",
        "region": settings.aws_default_region,
        "capabilities": ["list-buckets", "list-objects", "upload", "download", "delete"]
    }
