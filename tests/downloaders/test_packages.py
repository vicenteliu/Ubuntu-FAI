"""Tests for package downloader."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests

from src.downloaders.packages import PackageDownloader, PackageInfo, DownloadProgress


class TestPackageInfo:
    """Test PackageInfo model."""
    
    def test_valid_package_info(self, temp_dir):
        """Test valid package info creation."""
        package = PackageInfo(
            name="test-package",
            url="https://example.com/test.deb",
            sha256="abc123",
            size_bytes=1024,
            destination=temp_dir / "test.deb"
        )
        
        assert package.name == "test-package"
        assert str(package.url) == "https://example.com/test.deb"
        assert package.sha256 == "abc123"
        assert package.size_bytes == 1024
        assert package.destination == temp_dir / "test.deb"
    
    def test_package_info_without_optional_fields(self, temp_dir):
        """Test package info with only required fields."""
        package = PackageInfo(
            name="minimal-package",
            url="https://example.com/minimal.deb",
            destination=temp_dir / "minimal.deb"
        )
        
        assert package.name == "minimal-package"
        assert package.sha256 is None
        assert package.size_bytes is None


class TestDownloadProgress:
    """Test DownloadProgress model."""
    
    def test_download_progress(self):
        """Test download progress tracking."""
        progress = DownloadProgress(
            total_bytes=1000,
            downloaded_bytes=500,
            percentage=50.0,
            speed_mbps=1.5,
            eta_seconds=10
        )
        
        assert progress.total_bytes == 1000
        assert progress.downloaded_bytes == 500
        assert progress.percentage == 50.0
        assert progress.speed_mbps == 1.5
        assert progress.eta_seconds == 10


class TestPackageDownloader:
    """Test package downloader."""
    
    def setup_method(self):
        """Set up test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = PackageDownloader(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test method."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_downloader_initialization(self):
        """Test downloader initialization."""
        assert self.downloader.cache_dir == self.temp_dir
        assert self.downloader.chunk_size == 8192
        assert self.temp_dir.exists()
        assert hasattr(self.downloader, 'session')
        assert hasattr(self.downloader, 'logger')
    
    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        test_file = self.temp_dir / "test.txt"
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        calculated_hash = self.downloader._calculate_sha256(test_file)
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        assert calculated_hash == expected_hash
    
    def test_verify_file_success(self):
        """Test successful file verification."""
        test_file = self.temp_dir / "test.txt"
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        expected_size = len(test_content)
        
        is_valid = self.downloader._verify_file(
            test_file, 
            expected_hash, 
            expected_size
        )
        
        assert is_valid is True
    
    def test_verify_file_hash_mismatch(self):
        """Test file verification with hash mismatch."""
        test_file = self.temp_dir / "test.txt"
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        wrong_hash = "wronghash123"
        
        is_valid = self.downloader._verify_file(test_file, wrong_hash)
        
        assert is_valid is False
    
    def test_verify_file_size_mismatch(self):
        """Test file verification with size mismatch."""
        test_file = self.temp_dir / "test.txt"
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        wrong_size = 999
        
        is_valid = self.downloader._verify_file(test_file, None, wrong_size)
        
        assert is_valid is False
    
    def test_verify_nonexistent_file(self):
        """Test verification of non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.txt"
        
        is_valid = self.downloader._verify_file(nonexistent_file)
        
        assert is_valid is False
    
    @patch('src.downloaders.packages.requests.Session.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock response
        mock_response = Mock()
        mock_response.headers = {'content-length': '13'}
        mock_response.iter_content.return_value = [b"Hello, World!"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        test_url = "https://example.com/test.txt"
        destination = self.temp_dir / "downloaded.txt"
        
        self.downloader._download_file(test_url, destination)
        
        assert destination.exists()
        with open(destination, 'rb') as f:
            content = f.read()
        assert content == b"Hello, World!"
    
    @patch('src.downloaders.packages.requests.Session.get')
    def test_download_file_with_progress(self, mock_get):
        """Test file download with progress tracking."""
        # Mock response
        mock_response = Mock()
        mock_response.headers = {'content-length': '13'}
        mock_response.iter_content.return_value = [b"Hello", b", ", b"World!"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        progress_calls = []
        def progress_callback(progress):
            progress_calls.append(progress)
        
        test_url = "https://example.com/test.txt"
        destination = self.temp_dir / "downloaded.txt"
        
        self.downloader._download_file(test_url, destination, progress_callback)
        
        assert destination.exists()
        assert len(progress_calls) > 0
        
        # Check progress data
        for progress in progress_calls:
            assert isinstance(progress, DownloadProgress)
            assert progress.total_bytes == 13
    
    @patch('src.downloaders.packages.requests.Session.get')
    def test_download_package_success(self, mock_get):
        """Test successful package download."""
        test_content = b"fake deb package content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content.return_value = [test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        package = PackageInfo(
            name="test-package",
            url="https://example.com/test.deb",
            sha256=expected_hash,
            size_bytes=len(test_content),
            destination=self.temp_dir / "test.deb"
        )
        
        result_path = self.downloader.download_package(package)
        
        assert result_path.exists()
        assert result_path.name == "test.deb"
        
        # Verify content
        with open(result_path, 'rb') as f:
            downloaded_content = f.read()
        assert downloaded_content == test_content
    
    def test_download_package_cached(self):
        """Test package download using cached file."""
        # Create a cached file
        cached_file = self.temp_dir / "cached.deb"
        test_content = b"cached package content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with open(cached_file, 'wb') as f:
            f.write(test_content)
        
        package = PackageInfo(
            name="cached-package",
            url="https://example.com/cached.deb",
            sha256=expected_hash,
            size_bytes=len(test_content),
            destination=cached_file
        )
        
        # Should use cached file without downloading
        result_path = self.downloader.download_package(package)
        
        assert result_path == cached_file
        assert result_path.exists()
    
    @patch('src.downloaders.packages.requests.Session.get')
    def test_download_package_verification_failure(self, mock_get):
        """Test package download with verification failure."""
        test_content = b"fake package content"
        wrong_hash = "wronghash123"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content.return_value = [test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        package = PackageInfo(
            name="test-package",
            url="https://example.com/test.deb",
            sha256=wrong_hash,
            destination=self.temp_dir / "test.deb"
        )
        
        with pytest.raises(ValueError, match="verification failed"):
            self.downloader.download_package(package)
        
        # File should be cleaned up after failure
        assert not package.destination.exists()
    
    @patch('src.downloaders.packages.requests.Session.get')
    def test_download_packages_multiple(self, mock_get):
        """Test downloading multiple packages."""
        packages_data = [
            (b"package1 content", "pkg1.deb"),
            (b"package2 content", "pkg2.deb")
        ]
        
        # Mock responses for multiple calls
        responses = []
        for content, filename in packages_data:
            mock_response = Mock()
            mock_response.headers = {'content-length': str(len(content))}
            mock_response.iter_content.return_value = [content]
            mock_response.raise_for_status.return_value = None
            responses.append(mock_response)
        
        mock_get.side_effect = responses
        
        packages = []
        for i, (content, filename) in enumerate(packages_data):
            package = PackageInfo(
                name=f"package{i+1}",
                url=f"https://example.com/{filename}",
                sha256=hashlib.sha256(content).hexdigest(),
                destination=self.temp_dir / filename
            )
            packages.append(package)
        
        results = self.downloader.download_packages(packages)
        
        assert len(results) == 2
        assert "package1" in results
        assert "package2" in results
        
        for package in packages:
            assert package.destination.exists()
    
    def test_context_manager(self):
        """Test using downloader as context manager."""
        with PackageDownloader(self.temp_dir) as downloader:
            assert hasattr(downloader, 'session')
            assert downloader.session is not None
        
        # Session should be closed after context exit
        # Note: requests.Session.close() doesn't set any obvious flag,
        # so we just verify the context manager works without error