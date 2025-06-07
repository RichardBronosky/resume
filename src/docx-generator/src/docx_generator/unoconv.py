"""PDF conversion using docker-unoconv-webservice."""

import os
import time
import docker
import requests
from typing import Tuple, Optional
from pathlib import Path
from contextlib import contextmanager
import logging

# Configure logging - set higher level for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Silence other noisy loggers
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('docker').setLevel(logging.WARNING)

# Module-level storage for the active service
_active_service = None

class UnoconvService:
    """Manages a docker container running unoconv webservice."""
    
    def __init__(self, port: int = 3000):
        self.port = port
        self.client = docker.from_env()
        self.container = None
        
    def __enter__(self):
        """Start the container when entering context."""
        try:
            # Remove any existing container with the same name
            try:
                old_container = self.client.containers.get("unoconv")
                old_container.stop()
                old_container.remove()
            except docker.errors.NotFound:
                pass
            
            # Start new container
            logger.info("Starting new container...")
            self.container = self.client.containers.run(
                image="zrrrzzt/docker-unoconv-webservice",
                name="unoconv",
                ports={'3000/tcp': self.port},
                volumes={
                    os.getcwd(): {'bind': '/work', 'mode': 'rw'}
                },
                detach=True,
                remove=True
            )
            
            # Wait for service to be ready
            self._wait_for_service()
            logger.info("Container started")
            return self
            
        except Exception as e:
            raise RuntimeError(f"Failed to start unoconv service: {str(e)}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the container when exiting context."""
        if self.container:
            try:
                logger.info("Stopping container...")
                self.container.stop(timeout=0)  # Force immediate stop
                logger.info("Container stopped")
            except:
                pass  # Best effort to stop
    
    def _wait_for_service(self, timeout: int = 30, interval: float = 0.5):
        """Wait for the service to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try a basic GET request to the root endpoint instead of /health
                response = requests.get(f"http://localhost:{self.port}/")
                if response.status_code in (200, 404):  # 404 is fine, it means the server is up
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(interval)
        raise TimeoutError("Unoconv service failed to start")

@contextmanager
def get_service():
    """Get or create a UnoconvService instance."""
    global _active_service
    if _active_service is None:
        with UnoconvService() as service:
            _active_service = service
            try:
                yield service
            finally:
                _active_service = None
    else:
        yield _active_service

def get_active_service() -> Optional[UnoconvService]:
    """Get the currently active service instance, if any."""
    return _active_service

def docx_to_pdf(input_file: str) -> Tuple[bool, str]:
    """
    Convert a DOCX file to PDF using unoconv webservice.
    
    Args:
        input_file: Path to the input DOCX file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            return False, f"Input file not found: {input_file}"
        
        output_file = str(input_path.with_suffix('.pdf'))
        
        # Make input path relative to current directory for docker volume
        rel_input = os.path.relpath(input_file)
        rel_output = os.path.relpath(output_file)
        
        # Convert paths for use inside container
        container_input = f"/work/{rel_input}"
        
        # Get the active service or create a temporary one
        service = get_active_service()
        if service:
            files = {'file': (container_input, open(input_file, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(
                f"http://localhost:{service.port}/unoconv/pdf",
                files=files
            )
        else:
            with get_service() as temp_service:
                files = {'file': (container_input, open(input_file, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                response = requests.post(
                    f"http://localhost:{temp_service.port}/unoconv/pdf",
                    files=files
                )
        
        if response.status_code != 200:
            return False, f"Conversion failed with status {response.status_code}: {response.text}"
        
        # Save the PDF
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        return True, f"Successfully converted to {output_file}"
        
    except Exception as e:
        return False, f"Error converting to PDF: {str(e)}" 