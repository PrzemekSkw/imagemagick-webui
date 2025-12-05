"""
Background tasks for image processing
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from rq import get_current_job

from app.services.imagemagick import imagemagick_service
from app.services.file_service import file_service
from app.core.config import settings


def process_images(
    input_files: List[str],
    operations: List[Dict],
    output_format: str = "webp",
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process multiple images with specified operations
    Returns dict with output_files and status
    """
    job = get_current_job()
    results = {
        "success": [],
        "failed": [],
        "output_files": [],
    }
    
    total = len(input_files)
    
    for i, input_path in enumerate(input_files):
        try:
            # Update progress
            progress = int((i / total) * 100)
            if job:
                job.meta["progress"] = progress
                job.meta["current_file"] = Path(input_path).name
                job.save_meta()
            
            # Validate input file
            if not imagemagick_service.validate_file(input_path):
                results["failed"].append({
                    "file": input_path,
                    "error": "Invalid input file"
                })
                continue
            
            # Generate output path
            output_path = file_service.get_output_path(
                Path(input_path).name,
                output_format,
                user_id
            )
            
            # Execute (run async in sync context)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Build command (async)
                command = loop.run_until_complete(
                    imagemagick_service.build_command(
                        input_path,
                        output_path,
                        operations
                    )
                )
                
                # Execute command
                success, stdout, stderr = loop.run_until_complete(
                    imagemagick_service.execute(command)
                )
            finally:
                loop.close()
            
            if success and Path(output_path).exists():
                results["success"].append(input_path)
                results["output_files"].append(output_path)
            else:
                results["failed"].append({
                    "file": input_path,
                    "error": stderr or "Unknown error"
                })
                
        except Exception as e:
            results["failed"].append({
                "file": input_path,
                "error": str(e)
            })
    
    # Update final progress
    if job:
        job.meta["progress"] = 100
        job.meta["current_file"] = None
        job.save_meta()
    
    return results


def process_raw_command(
    input_files: List[str],
    raw_command: str,
    output_format: str = "png",
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process images with raw ImageMagick command (terminal mode)
    """
    job = get_current_job()
    results = {
        "success": [],
        "failed": [],
        "output_files": [],
    }
    
    total = len(input_files)
    
    for i, input_path in enumerate(input_files):
        try:
            # Update progress
            progress = int((i / total) * 100)
            if job:
                job.meta["progress"] = progress
                job.meta["current_file"] = Path(input_path).name
                job.save_meta()
            
            # Generate output path
            output_path = file_service.get_output_path(
                Path(input_path).name,
                output_format,
                user_id
            )
            
            # Execute
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Build command from raw input (async)
                command, error = loop.run_until_complete(
                    imagemagick_service.build_raw_command(
                        input_path,
                        output_path,
                        raw_command
                    )
                )
                
                if error:
                    results["failed"].append({
                        "file": input_path,
                        "error": error
                    })
                    continue
                
                # Execute command
                success, stdout, stderr = loop.run_until_complete(
                    imagemagick_service.execute(command)
                )
            finally:
                loop.close()
            
            if success and Path(output_path).exists():
                results["success"].append(input_path)
                results["output_files"].append(output_path)
            else:
                results["failed"].append({
                    "file": input_path,
                    "error": stderr or "Unknown error"
                })
                
        except Exception as e:
            results["failed"].append({
                "file": input_path,
                "error": str(e)
            })
    
    # Update final progress
    if job:
        job.meta["progress"] = 100
        job.meta["current_file"] = None
        job.save_meta()
    
    return results


def process_background_removal(
    input_files: List[str],
    output_format: str = "png",
    alpha_matting: bool = False,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Remove background from images using AI (rembg)
    """
    job = get_current_job()
    results = {
        "success": [],
        "failed": [],
        "output_files": [],
    }
    
    total = len(input_files)
    
    # Import AI service
    from app.services.ai_service import ai_service
    
    for i, input_path in enumerate(input_files):
        try:
            # Update progress
            progress = int((i / total) * 100)
            if job:
                job.meta["progress"] = progress
                job.meta["current_file"] = Path(input_path).name
                job.save_meta()
            
            # Generate output path (always PNG for transparency)
            output_path = file_service.get_output_path(
                Path(input_path).name,
                "png",  # Force PNG for transparency
                user_id
            )
            
            # Execute AI background removal
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result_path = loop.run_until_complete(
                    ai_service.remove_background(
                        input_path,
                        output_path,
                        alpha_matting=alpha_matting
                    )
                )
                
                if result_path and Path(result_path).exists():
                    results["success"].append(input_path)
                    results["output_files"].append(result_path)
                else:
                    results["failed"].append({
                        "file": input_path,
                        "error": "Background removal failed"
                    })
            finally:
                loop.close()
                
        except Exception as e:
            results["failed"].append({
                "file": input_path,
                "error": str(e)
            })
    
    # Final progress for bg removal
    if job:
        job.meta["progress"] = 100
        job.meta["current_file"] = None
        job.save_meta()
    
    return results
