"""Utility functions for downloaders."""

import logging
import time
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse
import requests


class DownloadError(Exception):
    """Exception raised when download operations fail."""
    pass


class ProgressTracker:
    """Tracks and logs download progress."""
    
    def __init__(self, name: str, total_size: int = 0):
        """Initialize progress tracker.
        
        Args:
            name: Name of the download
            total_size: Total expected size in bytes
        """
        self.name = name
        self.total_size = total_size
        self.downloaded = 0
        self.start_time = time.time()
        self.last_update = 0
        self.logger = logging.getLogger(__name__)
    
    def update(self, bytes_downloaded: int) -> None:
        """Update progress with newly downloaded bytes.
        
        Args:
            bytes_downloaded: Number of bytes downloaded in this update
        """
        self.downloaded += bytes_downloaded
        current_time = time.time()
        
        # Log progress every 5 seconds or when complete
        if (current_time - self.last_update > 5.0 or 
            (self.total_size > 0 and self.downloaded >= self.total_size)):
            
            self._log_progress()
            self.last_update = current_time
    
    def _log_progress(self) -> None:
        """Log current progress."""
        elapsed = time.time() - self.start_time
        
        if self.total_size > 0:
            percentage = (self.downloaded / self.total_size) * 100
            speed_mbps = (self.downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            
            self.logger.info(
                f"{self.name}: {percentage:.1f}% "
                f"({self.downloaded:,}/{self.total_size:,} bytes) "
                f"@ {speed_mbps:.1f} MB/s"
            )
        else:
            speed_mbps = (self.downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            self.logger.info(
                f"{self.name}: {self.downloaded:,} bytes downloaded "
                f"@ {speed_mbps:.1f} MB/s"
            )


def download_with_retry(url: str, destination: Path, 
                       max_retries: int = 3,
                       timeout: int = 30,
                       chunk_size: int = 8192,
                       progress_callback: Optional[Callable] = None) -> None:
    """Download a file with retry logic and progress tracking.
    
    Args:
        url: URL to download
        destination: Local destination path
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        chunk_size: Download chunk size in bytes
        progress_callback: Optional progress callback function
        
    Raises:
        DownloadError: If download fails after all retries
    """
    logger = logging.getLogger(__name__)
    
    # Create destination directory
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries + 1})")
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Ubuntu-FAI-Builder/1.0'
            })
            
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            progress_tracker = ProgressTracker(
                name=destination.name,
                total_size=total_size
            )
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress_tracker.update(len(chunk))
                        
                        if progress_callback:
                            progress_callback(progress_tracker)
            
            logger.info(f"Successfully downloaded {url} to {destination}")
            return
            
        except (requests.RequestException, IOError) as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            
            # Clean up partial download
            if destination.exists():
                destination.unlink()
            
            if attempt < max_retries:
                # Exponential backoff
                sleep_time = 2 ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise DownloadError(f"Failed to download {url} after {max_retries + 1} attempts: {e}")


def get_filename_from_url(url: str, default_name: str = "download") -> str:
    """Extract filename from URL.
    
    Args:
        url: URL to extract filename from
        default_name: Default filename if extraction fails
        
    Returns:
        Extracted or default filename
    """
    parsed = urlparse(url)
    path = Path(parsed.path)
    
    if path.name:
        return path.name
    else:
        return default_name


def validate_url(url: str) -> bool:
    """Validate if a URL is well-formed and accessible.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and accessible
    """
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # Check if URL is accessible with HEAD request
        response = requests.head(url, timeout=10)
        return response.status_code < 400
        
    except requests.RequestException:
        return False


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hash as hex string
        
    Raises:
        ValueError: If algorithm is not supported
    """
    import hashlib
    
    try:
        hasher = getattr(hashlib, algorithm)()
    except AttributeError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def clean_directory(directory: Path, max_age_days: int = 30, 
                   pattern: str = "*") -> int:
    """Clean old files from a directory.
    
    Args:
        directory: Directory to clean
        max_age_days: Maximum age of files in days
        pattern: File pattern to match
        
    Returns:
        Number of files removed
    """
    import time
    
    if not directory.exists():
        return 0
    
    cutoff_time = time.time() - (max_age_days * 24 * 3600)
    removed_count = 0
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            file_path.unlink()
            removed_count += 1
    
    return removed_count