"""Package downloader with caching and verification for Ubuntu FAI builds."""

import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import requests
from pydantic import BaseModel, Field, HttpUrl

from ..config.models import PackageConfig


class DownloadProgress(BaseModel):
    """Progress tracking for downloads."""
    
    total_bytes: int = 0
    downloaded_bytes: int = 0
    percentage: float = 0.0
    speed_mbps: float = 0.0
    eta_seconds: Optional[int] = None


class PackageInfo(BaseModel):
    """Information about a downloadable package."""
    
    name: str = Field(..., description="Package name")
    url: HttpUrl = Field(..., description="Download URL")
    sha256: Optional[str] = Field(None, description="Expected SHA256 hash")
    size_bytes: Optional[int] = Field(None, description="Expected file size")
    destination: Path = Field(..., description="Local destination path")


class PackageDownloader:
    """Downloads and caches package files with verification."""
    
    def __init__(self, cache_dir: Path, chunk_size: int = 8192):
        """Initialize package downloader.
        
        Args:
            cache_dir: Directory for caching downloaded files
            chunk_size: Download chunk size in bytes
        """
        self.cache_dir = Path(cache_dir)
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ubuntu-FAI-Builder/1.0'
        })
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def _verify_file(self, file_path: Path, expected_sha256: Optional[str] = None, 
                    expected_size: Optional[int] = None) -> bool:
        """Verify downloaded file integrity.
        
        Args:
            file_path: Path to downloaded file
            expected_sha256: Expected SHA256 hash
            expected_size: Expected file size in bytes
            
        Returns:
            True if file is valid
        """
        if not file_path.exists():
            return False
            
        # Check file size
        if expected_size is not None:
            actual_size = file_path.stat().st_size
            if actual_size != expected_size:
                self.logger.warning(
                    f"Size mismatch for {file_path}: expected {expected_size}, got {actual_size}"
                )
                return False
        
        # Check SHA256 hash
        if expected_sha256 is not None:
            actual_sha256 = self._calculate_sha256(file_path)
            if actual_sha256 != expected_sha256:
                self.logger.warning(
                    f"SHA256 mismatch for {file_path}: expected {expected_sha256}, got {actual_sha256}"
                )
                return False
                
        return True
    
    def _download_file(self, url: str, destination: Path, 
                      progress_callback: Optional[callable] = None) -> None:
        """Download a file with progress tracking.
        
        Args:
            url: URL to download
            destination: Local destination path
            progress_callback: Optional progress callback function
        """
        self.logger.info(f"Downloading {url} to {destination}")
        
        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = DownloadProgress(
                            total_bytes=total_size,
                            downloaded_bytes=downloaded,
                            percentage=(downloaded / total_size) * 100
                        )
                        progress_callback(progress)
    
    def download_package(self, package: PackageInfo, 
                        force_download: bool = False,
                        progress_callback: Optional[callable] = None) -> Path:
        """Download a single package with caching.
        
        Args:
            package: Package information
            force_download: Force re-download even if cached
            progress_callback: Optional progress callback
            
        Returns:
            Path to downloaded file
            
        Raises:
            requests.RequestException: If download fails
            ValueError: If file verification fails
        """
        # Determine cache file path
        url_path = urlparse(str(package.url)).path
        filename = Path(url_path).name or package.name
        cache_path = self.cache_dir / filename
        
        # Check if file exists and is valid
        if not force_download and cache_path.exists():
            if self._verify_file(cache_path, package.sha256, package.size_bytes):
                self.logger.info(f"Using cached file: {cache_path}")
                return cache_path
            else:
                self.logger.warning(f"Cached file verification failed: {cache_path}")
                cache_path.unlink()  # Remove invalid file
        
        # Download file
        try:
            self._download_file(str(package.url), cache_path, progress_callback)
            
            # Verify downloaded file
            if not self._verify_file(cache_path, package.sha256, package.size_bytes):
                cache_path.unlink()  # Remove invalid file
                raise ValueError(f"Downloaded file verification failed: {cache_path}")
                
            self.logger.info(f"Successfully downloaded and verified: {cache_path}")
            return cache_path
            
        except Exception as e:
            if cache_path.exists():
                cache_path.unlink()  # Clean up on failure
            raise
    
    def download_packages(self, packages: List[PackageInfo],
                         parallel: bool = False,
                         progress_callback: Optional[callable] = None) -> Dict[str, Path]:
        """Download multiple packages.
        
        Args:
            packages: List of packages to download
            parallel: Whether to download in parallel (not implemented)
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary mapping package names to downloaded file paths
        """
        results = {}
        
        for i, package in enumerate(packages):
            self.logger.info(f"Downloading package {i+1}/{len(packages)}: {package.name}")
            
            try:
                file_path = self.download_package(package, progress_callback=progress_callback)
                results[package.name] = file_path
                
            except Exception as e:
                self.logger.error(f"Failed to download {package.name}: {e}")
                raise
        
        return results
    
    def create_package_info_from_config(self, config: PackageConfig) -> List[PackageInfo]:
        """Create PackageInfo objects from configuration.
        
        Args:
            config: Package configuration
            
        Returns:
            List of PackageInfo objects
        """
        packages = []
        
        # Handle custom DEB packages from URLs
        for i, deb_url in enumerate(config.deb_urls):
            # Extract filename from URL
            url_path = urlparse(deb_url).path
            filename = Path(url_path).name or f"package_{i}.deb"
            package_name = filename.replace('.deb', '')
            
            packages.append(PackageInfo(
                name=package_name,
                url=deb_url,
                sha256=None,  # No checksum validation for simple URLs
                size_bytes=None,
                destination=self.cache_dir / filename
            ))
        
        # Note: snap_packages are handled by the system package manager,
        # not as downloadable assets, so we don't process them here
        
        return packages
    
    def cleanup_cache(self, max_age_days: int = 30) -> None:
        """Clean up old cached files.
        
        Args:
            max_age_days: Maximum age of cached files in days
        """
        import time
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        for file_path in self.cache_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                self.logger.info(f"Removing old cached file: {file_path}")
                file_path.unlink()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()