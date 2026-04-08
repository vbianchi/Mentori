from fastapi import APIRouter, Depends, HTTPException
import psutil
import os
from typing import List
from pydantic import BaseModel
from backend.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/system", tags=["system"])

class SystemStats(BaseModel):
    cpu_percent: float
    memory: dict
    disk: dict

@router.get("/stats", response_model=SystemStats)
def get_system_stats(current_user: User = Depends(get_current_user)):
    """
    Get system resource usage. Available to all authenticated users.
    """
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory": {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "percent": disk.percent
        }
    }

@router.get("/logs", response_model=List[str])
def get_system_logs(lines: int = 100, current_user: User = Depends(get_current_user)):
    """
    Get recent backend logs. Admin only. 
    (Note: For now, we mock this or read from a known file if setup. 
    Ideally, we'd read from supervisord or a log file)
    """
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    log_file = "backend/logs/app.log"
    if not os.path.exists(log_file):
        # Fallback if no file logger configured yet
        return ["Log file not found. Ensure logging is configured to write to backend/logs/app.log"]
    
    try:
        with open(log_file, "r") as f:
            # Efficiently read last N lines
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception as e:
        return [f"Error reading logs: {str(e)}"]
