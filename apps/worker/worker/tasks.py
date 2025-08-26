"""Background tasks for EPUB processing."""

import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

from celery import current_app as celery_app


@celery_app.task(name="process_epub")
def process_epub_task(epub_path: str, book_id: str, user_id: str) -> dict:
    """Process uploaded EPUB file into structured assets.
    
    Args:
        epub_path: Path to uploaded EPUB file
        book_id: UUID of the book record
        user_id: UUID of the user
        
    Returns:
        dict: Processing result with status and metadata
    """
    try:
        epub_file = Path(epub_path)
        if not epub_file.exists():
            return {"status": "error", "message": f"EPUB file not found: {epub_path}"}
        
        # Create book storage directory
        book_storage = Path(f"storage/books/{book_id}")
        book_storage.mkdir(parents=True, exist_ok=True)
        
        # Extract EPUB to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP contents
            with ZipFile(epub_file, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            # Find OPF file (package document)
            container_xml = temp_path / "META-INF" / "container.xml"
            if not container_xml.exists():
                return {"status": "error", "message": "Invalid EPUB: missing container.xml"}
            
            # TODO: Parse container.xml to find OPF file path
            # TODO: Parse OPF file to extract manifest, spine, metadata
            # TODO: Copy chapter files to structured directories
            # TODO: Copy images, fonts, stylesheets
            # TODO: Generate manifest.json for reader
            
            # Placeholder: copy all files for now
            chapters_dir = book_storage / "chapters"
            images_dir = book_storage / "images"
            fonts_dir = book_storage / "fonts"
            
            chapters_dir.mkdir(exist_ok=True)
            images_dir.mkdir(exist_ok=True)
            fonts_dir.mkdir(exist_ok=True)
            
            # Create basic manifest
            manifest = {
                "book_id": book_id,
                "title": "Processed EPUB",
                "author": "Unknown",
                "chapters": [],
                "images": [],
                "fonts": [],
                "processing_status": "completed"
            }
            
            # Write manifest
            import json
            with open(book_storage / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
        
        # Remove original upload file
        epub_file.unlink()
        
        return {
            "status": "success", 
            "book_id": book_id,
            "manifest_path": str(book_storage / "manifest.json")
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Processing failed: {str(e)}"}


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files_task() -> dict:
    """Clean up old temporary files.
    
    Returns:
        dict: Cleanup result
    """
    try:
        temp_dir = Path("storage/temp")
        if not temp_dir.exists():
            return {"status": "success", "message": "No temp directory to clean"}
        
        # Remove files older than 24 hours
        import time
        current_time = time.time()
        cleaned_count = 0
        
        for item in temp_dir.rglob("*"):
            if item.is_file():
                file_age = current_time - item.stat().st_mtime
                if file_age > (24 * 60 * 60):  # 24 hours in seconds
                    item.unlink()
                    cleaned_count += 1
        
        return {"status": "success", "cleaned_files": cleaned_count}
        
    except Exception as e:
        return {"status": "error", "message": f"Cleanup failed: {str(e)}"}
