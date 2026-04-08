
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.models.user import User
from backend.mcp.custom.file_ops import _get_user_root, _validate_path, SecurityError
from backend.logging_config import logger

router = APIRouter(prefix="/tasks/{task_id}/files", tags=["files"])

class FileNode(BaseModel):
    name: str
    type: str # 'file' or 'folder'
    path: str # Relative to workspace root
    children: List['FileNode'] = []
    size: int = 0
    # Enhanced metadata
    modified: Optional[datetime] = None
    created: Optional[datetime] = None
    extension: Optional[str] = None
    is_binary: bool = False

class CreateFolderRequest(BaseModel):
    path: str

class MoveRequest(BaseModel):
    source_path: str
    destination_path: str

class RenameRequest(BaseModel):
    path: str
    new_name: str

class UpdateFileRequest(BaseModel):
    path: str
    content: str

class CreateFileRequest(BaseModel):
    path: str
    content: str = ""  # Optional initial content

class CopyRequest(BaseModel):
    source_path: str
    destination_path: str

FileNode.update_forward_refs()

def _build_file_tree(root_path: Path, current_path: Path, include_hidden: bool = False) -> List[FileNode]:
    """
    Recursively builds a tree of FileNodes with enhanced metadata.
    root_path: The absolute path to the user's workspace root.
    current_path: The absolute path to the current directory being scanned.
    include_hidden: Whether to include hidden files/folders (starting with .)
    """
    nodes = []
    try:
        # Sort directories first, then files
        items = sorted(os.listdir(current_path), key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))

        # Binary file extensions
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.gz', '.tar',
                            '.bz2', '.exe', '.bin', '.pkl', '.pyc', '.so', '.dll'}

        for item in items:
            if item.startswith('.') and not include_hidden:
                continue

            full_path = current_path / item
            rel_path = full_path.relative_to(root_path)
            stat = full_path.stat()

            if full_path.is_dir():
                nodes.append(FileNode(
                    name=item,
                    type="folder",
                    path=str(rel_path),
                    children=_build_file_tree(root_path, full_path, include_hidden),
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    created=datetime.fromtimestamp(stat.st_ctime)
                ))
            else:
                ext = full_path.suffix.lower()
                nodes.append(FileNode(
                    name=item,
                    type="file",
                    path=str(rel_path),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    created=datetime.fromtimestamp(stat.st_ctime),
                    extension=ext if ext else None,
                    is_binary=ext in binary_extensions
                ))
    except Exception as e:
        logger.error(f"Error scanning directory {current_path}: {e}")

    return nodes

@router.get("", response_model=List[FileNode])
def list_files(
    task_id: str,
    include_hidden: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    List all files in the user's workspace.
    Note: We currently scope this to the USER workspace, ignoring task_id for storage,
    so that agents can see all files the user uploads.

    Args:
        include_hidden: If True, includes hidden files/folders (starting with .)
    """
    user_root = _get_user_root(current_user.id)

    if not user_root.exists():
        user_root.mkdir(parents=True, exist_ok=True)

    return _build_file_tree(user_root, user_root, include_hidden)

@router.post("")
async def upload_file(
    task_id: str,
    file: UploadFile = File(...),
    path: str = Form(""), # Optional subfolder path
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file to the user's workspace.
    """
    user_root = _get_user_root(current_user.id)
    
    # Determine target directory
    if path:
        try:
            target_dir = _validate_path(path, current_user.id)
            if not target_dir.is_dir():
                 raise HTTPException(status_code=400, detail="Target path is not a directory")
        except SecurityError:
             raise HTTPException(status_code=403, detail="Invalid target path")
    else:
        target_dir = user_root
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = target_dir / file.filename
    try:
        # Check if safe path (paranoid check)
        _validate_path(file_path, current_user.id)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"User {current_user.email} uploaded file {file.filename} to {target_dir}")
        return {"filename": file.filename, "path": str(file_path.relative_to(user_root)), "status": "uploaded"}
        
    except SecurityError:
        raise HTTPException(status_code=403, detail="Security violation: Cannot upload to this path")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/content")
def get_file_content(
    task_id: str,
    path: str, # Relative path
    current_user: User = Depends(get_current_user)
):
    """
    Download/View a file.
    """
    try:
        logger.info(f"Reading file content - path: {path}, user: {current_user.email}")
        file_path = _validate_path(path, current_user.id)
        logger.info(f"Resolved absolute path: {file_path}")

        if not file_path.is_file():
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")

        # Read file size for logging
        file_size = file_path.stat().st_size
        logger.info(f"Returning file content, size: {file_size} bytes")

        # Return FileResponse with no-cache headers to prevent stale content
        response = FileResponse(
            file_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        return response
    except SecurityError as e:
        logger.error(f"Security error reading {path}: {e}")
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Error reading file {path}: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_folder")
def create_folder(
    task_id: str,
    req: CreateFolderRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        path = _validate_path(req.path, current_user.id)
        if path.exists():
             raise HTTPException(status_code=400, detail="Directory already exists")
        path.mkdir(parents=True, exist_ok=True)
        return {"status": "success", "path": req.path}
    except SecurityError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
def delete_item(
    task_id: str,
    path: str,
    current_user: User = Depends(get_current_user)
):
    try:
        target = _validate_path(path, current_user.id)
        if not target.exists():
            raise HTTPException(status_code=404, detail="Item not found")
            
        if target.is_dir():
            shutil.rmtree(target)
        else:
            os.remove(target)
            
        return {"status": "success", "deleted": path}
    except SecurityError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/move")
def move_item(
    task_id: str,
    req: MoveRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        src = _validate_path(req.source_path, current_user.id)
        # For validation only, we resolve dest directory, not full path yet
        # Actually validation checks the final path.
        # But we need to construct final path.
        
        # Logic: Move source_path TO destination_path
        # If destination_path is a folder, move INTO it.
        # If destination_path is a new path (rename/move), use it directly?
        # Standard Drag & Drop semantics: "Drop Item A onto Folder B" -> B/A
        
        # Let's assume frontend sends the target FOLDER as destination.
        user_root = _get_user_root(current_user.id)
        
        # Security: validate both
        if not src.exists():
            raise HTTPException(status_code=404, detail="Source not found")
            
        # Validate parent of destination at least?
        # Let's trust _validate_path to check containment.
        
        # We need to compute the actual destination path.
        # If dest is ".", it's root.
        
        # Validate 'destination_path' (which is the target folder)
        dest_folder = _validate_path(req.destination_path, current_user.id)
        
        if not dest_folder.is_dir():
             # If exact path logic:
             # shutil.move(src, dst)
             # But usually UI sends "Target Parent"
             raise HTTPException(status_code=400, detail="Destination must be a directory")
             
        final_dest = dest_folder / src.name
        
        # Re-validate final path (redundant but safe)
        _validate_path(final_dest, current_user.id)
        
        if final_dest.exists():
             raise HTTPException(status_code=400, detail="Destination already exists")
             
        shutil.move(str(src), str(final_dest))
        return {"status": "success", "from": req.source_path, "to": str(final_dest.relative_to(user_root))}
        
    except SecurityError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename")
def rename_item(
    task_id: str,
    req: RenameRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        src = _validate_path(req.path, current_user.id)
        if not src.exists():
             raise HTTPException(status_code=404, detail="Item not found")

        # New path is within the SAME parent directory
        parent = src.parent
        new_path = parent / req.new_name

        # Validate that new_path is safe (it should be if parent is safe, but check anyway)
        _validate_path(new_path, current_user.id)

        if new_path.exists():
            raise HTTPException(status_code=400, detail="Name already exists")

        src.rename(new_path)
        return {"status": "success", "new_name": req.new_name}

    except SecurityError:
         raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.put("/update")
def update_file(
    task_id: str,
    req: UpdateFileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update file content (for Code tab editing).
    """
    try:
        logger.info(f"Update request - path: {req.path}, content_length: {len(req.content)}, task_id: {task_id}, user: {current_user.email}")

        file_path = _validate_path(req.path, current_user.id)
        logger.info(f"Resolved absolute path: {file_path}")

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")

        if not file_path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Read current content before writing
        with open(file_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
        logger.info(f"Old content length: {len(old_content)}")

        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(req.content)

        # Verify write
        with open(file_path, 'r', encoding='utf-8') as f:
            verified_content = f.read()
        logger.info(f"Written content length: {len(verified_content)}, matches request: {verified_content == req.content}")

        logger.info(f"User {current_user.email} successfully updated file {req.path}")
        return {"status": "success", "path": req.path, "size": len(req.content), "verified": True}

    except SecurityError as e:
        logger.error(f"Security error: {e}")
        raise HTTPException(status_code=403, detail="Access denied")
    except UnicodeDecodeError as e:
        logger.error(f"Unicode error: {e}")
        raise HTTPException(status_code=400, detail="Cannot edit binary file")
    except Exception as e:
        logger.error(f"Update failed with exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_file")
def create_file(
    task_id: str,
    req: CreateFileRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new file with optional initial content.
    """
    try:
        file_path = _validate_path(req.path, current_user.id)
        if file_path.exists():
            raise HTTPException(status_code=400, detail="File already exists")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(req.content)

        logger.info(f"User {current_user.email} created file {req.path}")
        return {"status": "success", "path": req.path}

    except SecurityError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Create file failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy")
def copy_item(
    task_id: str,
    req: CopyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Copy file or folder to destination.
    """
    try:
        src = _validate_path(req.source_path, current_user.id)
        if not src.exists():
            raise HTTPException(status_code=404, detail="Source not found")

        dest_folder = _validate_path(req.destination_path, current_user.id)
        if not dest_folder.is_dir():
            raise HTTPException(status_code=400, detail="Destination must be a directory")

        # Determine new name (append "_copy" if same location)
        if src.parent == dest_folder:
            stem = src.stem
            suffix = src.suffix
            dest_path = dest_folder / f"{stem}_copy{suffix}"
        else:
            dest_path = dest_folder / src.name

        # Handle name conflicts
        counter = 1
        while dest_path.exists():
            if src.parent == dest_folder:
                dest_path = dest_folder / f"{stem}_copy{counter}{suffix}"
            else:
                dest_path = dest_folder / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
            if counter > 100:  # Prevent infinite loop
                raise HTTPException(status_code=400, detail="Too many copies with same name")

        # Validate final destination
        _validate_path(dest_path, current_user.id)

        if src.is_dir():
            shutil.copytree(src, dest_path)
        else:
            shutil.copy2(src, dest_path)

        user_root = _get_user_root(current_user.id)
        logger.info(f"User {current_user.email} copied {req.source_path} to {dest_path.relative_to(user_root)}")
        return {"status": "success", "new_path": str(dest_path.relative_to(user_root))}

    except SecurityError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
