"""Script downloader with validation and caching for Ubuntu FAI builds."""

import hashlib
import logging
import stat
from pathlib import Path
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse
import requests
from pydantic import BaseModel, Field, HttpUrl

from ..config.models import FirstBootConfig


class ScriptInfo(BaseModel):
    """Information about a downloadable script."""
    
    name: str = Field(..., description="Script name")
    url: HttpUrl = Field(..., description="Download URL")
    sha256: Optional[str] = Field(None, description="Expected SHA256 hash")
    executable: bool = Field(True, description="Whether script should be executable")
    interpreter: Optional[str] = Field(None, description="Script interpreter (bash, python, etc.)")
    destination: Path = Field(..., description="Local destination path")


class ScriptValidator:
    """Validates downloaded scripts for security and correctness."""
    
    # Allowed script interpreters
    ALLOWED_INTERPRETERS = {
        'bash', 'sh', 'python', 'python3', 'perl', 'ruby'
    }
    
    # Dangerous patterns that should trigger warnings
    DANGEROUS_PATTERNS = {
        'rm -rf /',
        'dd if=',
        'mkfs.',
        'fdisk',
        'parted',
        'curl.*|.*bash',
        'wget.*|.*bash',
        'eval',
        'exec',
        '> /dev/',
        'chmod 777'
    }
    
    def __init__(self):
        """Initialize script validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_script_content(self, script_path: Path) -> Dict[str, any]:
        """Validate script content for security issues.
        
        Args:
            script_path: Path to script file
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'interpreter': None,
            'line_count': 0
        }
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                results['line_count'] = len(lines)
                
                # Check shebang line
                if lines and lines[0].startswith('#!'):
                    shebang = lines[0][2:].strip()
                    interpreter = Path(shebang.split()[0]).name
                    results['interpreter'] = interpreter
                    
                    if interpreter not in self.ALLOWED_INTERPRETERS:
                        results['warnings'].append(
                            f"Unusual interpreter: {interpreter}"
                        )
                
                # Check for dangerous patterns
                content_lower = content.lower()
                for pattern in self.DANGEROUS_PATTERNS:
                    if pattern.lower() in content_lower:
                        results['warnings'].append(
                            f"Potentially dangerous pattern found: {pattern}"
                        )
                
                # Check script size (warn if too large)
                if len(content) > 100000:  # 100KB
                    results['warnings'].append(
                        f"Script is large ({len(content)} bytes)"
                    )
                
        except UnicodeDecodeError:
            results['errors'].append("Script contains non-UTF-8 content")
            results['is_valid'] = False
        except Exception as e:
            results['errors'].append(f"Error reading script: {e}")
            results['is_valid'] = False
        
        return results
    
    def validate_script_syntax(self, script_path: Path, interpreter: str) -> bool:
        """Validate script syntax using appropriate interpreter.
        
        Args:
            script_path: Path to script file
            interpreter: Script interpreter
            
        Returns:
            True if syntax is valid
        """
        import subprocess
        
        try:
            if interpreter in ['bash', 'sh']:
                # Use bash -n for syntax checking
                result = subprocess.run(
                    ['bash', '-n', str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
                
            elif interpreter in ['python', 'python3']:
                # Use python -m py_compile for syntax checking
                result = subprocess.run(
                    [interpreter, '-m', 'py_compile', str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.warning(f"Could not validate syntax for {script_path}")
            
        return True  # Assume valid if we can't check


class ScriptDownloader:
    """Downloads and validates script files with caching."""
    
    def __init__(self, cache_dir: Path, validate_scripts: bool = True):
        """Initialize script downloader.
        
        Args:
            cache_dir: Directory for caching downloaded scripts
            validate_scripts: Whether to validate downloaded scripts
        """
        self.cache_dir = Path(cache_dir)
        self.validate_scripts = validate_scripts
        self.validator = ScriptValidator() if validate_scripts else None
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
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def _set_executable(self, file_path: Path) -> None:
        """Set executable permissions on a file.
        
        Args:
            file_path: Path to file
        """
        current_mode = file_path.stat().st_mode
        new_mode = current_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
        file_path.chmod(new_mode)
    
    def _download_script(self, url: str, destination: Path) -> None:
        """Download a script file.
        
        Args:
            url: URL to download
            destination: Local destination path
        """
        self.logger.info(f"Downloading script {url} to {destination}")
        
        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            f.write(response.content)
    
    def download_script(self, script: ScriptInfo, 
                       force_download: bool = False,
                       validate: bool = None) -> Path:
        """Download a single script with validation.
        
        Args:
            script: Script information
            force_download: Force re-download even if cached
            validate: Override validation setting
            
        Returns:
            Path to downloaded script
            
        Raises:
            requests.RequestException: If download fails
            ValueError: If script validation fails
        """
        # Determine cache file path
        url_path = urlparse(str(script.url)).path
        filename = Path(url_path).name or f"{script.name}.sh"
        cache_path = self.cache_dir / filename
        
        # Check if file exists and is valid
        if not force_download and cache_path.exists():
            if script.sha256:
                actual_sha256 = self._calculate_sha256(cache_path)
                if actual_sha256 == script.sha256:
                    self.logger.info(f"Using cached script: {cache_path}")
                    
                    # Ensure executable permissions
                    if script.executable:
                        self._set_executable(cache_path)
                    
                    return cache_path
                else:
                    self.logger.warning(f"Cached script hash mismatch: {cache_path}")
                    cache_path.unlink()  # Remove invalid file
            else:
                self.logger.info(f"Using cached script (no hash check): {cache_path}")
                return cache_path
        
        # Download script
        try:
            self._download_script(str(script.url), cache_path)
            
            # Verify SHA256 hash if provided
            if script.sha256:
                actual_sha256 = self._calculate_sha256(cache_path)
                if actual_sha256 != script.sha256:
                    cache_path.unlink()  # Remove invalid file
                    raise ValueError(f"Script hash verification failed: {cache_path}")
            
            # Set executable permissions
            if script.executable:
                self._set_executable(cache_path)
            
            # Validate script content
            should_validate = validate if validate is not None else self.validate_scripts
            if should_validate and self.validator:
                validation_results = self.validator.validate_script_content(cache_path)
                
                if not validation_results['is_valid']:
                    cache_path.unlink()  # Remove invalid file
                    raise ValueError(
                        f"Script validation failed: {validation_results['errors']}"
                    )
                
                if validation_results['warnings']:
                    for warning in validation_results['warnings']:
                        self.logger.warning(f"Script {script.name}: {warning}")
                
                # Validate syntax if interpreter is known
                if validation_results['interpreter']:
                    if not self.validator.validate_script_syntax(
                        cache_path, validation_results['interpreter']
                    ):
                        self.logger.warning(f"Script {script.name} has syntax errors")
            
            self.logger.info(f"Successfully downloaded script: {cache_path}")
            return cache_path
            
        except Exception as e:
            if cache_path.exists():
                cache_path.unlink()  # Clean up on failure
            raise
    
    def download_scripts(self, scripts: List[ScriptInfo]) -> Dict[str, Path]:
        """Download multiple scripts.
        
        Args:
            scripts: List of scripts to download
            
        Returns:
            Dictionary mapping script names to downloaded file paths
        """
        results = {}
        
        for i, script in enumerate(scripts):
            self.logger.info(f"Downloading script {i+1}/{len(scripts)}: {script.name}")
            
            try:
                file_path = self.download_script(script)
                results[script.name] = file_path
                
            except Exception as e:
                self.logger.error(f"Failed to download script {script.name}: {e}")
                raise
        
        return results
    
    def create_script_info_from_config(self, config: FirstBootConfig) -> List[ScriptInfo]:
        """Create ScriptInfo objects from configuration.
        
        Args:
            config: First boot configuration
            
        Returns:
            List of ScriptInfo objects
        """
        scripts = []
        
        # Handle custom scripts
        for script_config in config.scripts:
            if hasattr(script_config, 'url') and script_config.url:
                scripts.append(ScriptInfo(
                    name=script_config.name,
                    url=script_config.url,
                    sha256=getattr(script_config, 'sha256', None),
                    executable=getattr(script_config, 'executable', True),
                    interpreter=getattr(script_config, 'interpreter', None),
                    destination=self.cache_dir / f"{script_config.name}.sh"
                ))
        
        return scripts
    
    def cleanup_cache(self, max_age_days: int = 30) -> None:
        """Clean up old cached scripts.
        
        Args:
            max_age_days: Maximum age of cached scripts in days
        """
        import time
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        for file_path in self.cache_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                self.logger.info(f"Removing old cached script: {file_path}")
                file_path.unlink()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()