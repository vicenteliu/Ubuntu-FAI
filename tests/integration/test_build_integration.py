"""Integration tests for the build system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from build import FAIBuilder


class TestBuildIntegration:
    """Integration tests for the complete build process."""
    
    def setup_method(self):
        """Set up test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "output"
        self.cache_dir = self.temp_dir / "cache"
    
    def teardown_method(self):
        """Clean up test method."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_builder_initialization(self, config_file):
        """Test FAI builder initialization."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        assert builder.config_path == config_file
        assert builder.output_dir == self.output_dir
        assert builder.cache_dir == self.cache_dir
        assert self.output_dir.exists()
        assert self.cache_dir.exists()
        
        # Check components are initialized
        assert builder.validator is not None
        assert builder.autoinstall_gen is not None
        assert builder.fai_config_gen is not None
        assert builder.first_boot_gen is not None
    
    def test_load_and_validate_config(self, config_file):
        """Test configuration loading and validation."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        config = builder.load_and_validate_config()
        
        assert config is not None
        assert builder.config is not None
        assert config == builder.config
        assert config.hardware.vendor == "Dell"
        assert config.user.username == "testuser"
    
    def test_load_invalid_config(self, temp_dir):
        """Test loading invalid configuration."""
        # Create invalid config file
        invalid_config = {
            "hardware": {
                "vendor": "",  # Invalid
                "model": "Test",
                "cpu_cores": -1,  # Invalid
                "memory_gb": 16,
                "storage_gb": 512
            }
        }
        
        invalid_config_file = temp_dir / "invalid_config.json"
        with open(invalid_config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        builder = FAIBuilder(
            config_path=invalid_config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        with pytest.raises(Exception):
            builder.load_and_validate_config()
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file."""
        nonexistent_file = self.temp_dir / "nonexistent.json"
        
        builder = FAIBuilder(
            config_path=nonexistent_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        with pytest.raises(Exception):
            builder.load_and_validate_config()
    
    @patch('src.downloaders.packages.PackageDownloader.download_packages')
    @patch('src.downloaders.scripts.ScriptDownloader.download_scripts')
    def test_download_assets(self, mock_download_scripts, mock_download_packages, config_file):
        """Test asset downloading."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        # Load config first
        builder.load_and_validate_config()
        
        # Mock successful downloads
        mock_download_packages.return_value = {"package1": Path("/cache/package1.deb")}
        mock_download_scripts.return_value = {"script1": Path("/cache/script1.sh")}
        
        # Should not raise any exceptions
        builder.download_assets()
        
        # Verify downloaders were called
        assert mock_download_packages.called or mock_download_scripts.called
    
    def test_generate_autoinstall_config(self, config_file):
        """Test autoinstall configuration generation."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        builder.load_and_validate_config()
        
        output_path = builder.generate_autoinstall_config()
        
        assert output_path.exists()
        assert output_path.name == "user-data.yaml"
        assert output_path.parent == self.output_dir
        
        # Verify content is valid YAML
        import yaml
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert isinstance(data, dict)
        assert 'autoinstall' in data
    
    def test_generate_fai_config(self, config_file):
        """Test FAI configuration generation."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        builder.load_and_validate_config()
        
        fai_config_dir = builder.generate_fai_config()
        
        assert fai_config_dir.exists()
        assert fai_config_dir.is_dir()
        assert fai_config_dir.name == "fai-config"
        assert fai_config_dir.parent == self.output_dir
        
        # Check for expected FAI structure
        expected_dirs = ["class", "files", "scripts", "package_config", "disk_config"]
        for expected_dir in expected_dirs:
            dir_path = fai_config_dir / expected_dir
            if dir_path.exists():  # Some dirs may be optional
                assert dir_path.is_dir()
    
    def test_generate_first_boot_config(self, config_file):
        """Test first-boot configuration generation."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        builder.load_and_validate_config()
        
        first_boot_dir = builder.generate_first_boot_config()
        
        assert first_boot_dir.exists()
        assert first_boot_dir.is_dir()
        assert first_boot_dir.name == "first-boot"
        assert first_boot_dir.parent == self.output_dir
        
        # Check for expected files
        service_file = first_boot_dir / "first-boot.service"
        script_file = first_boot_dir / "first-boot.sh"
        
        assert service_file.exists()
        assert script_file.exists()
        
        # Verify script is executable
        import stat
        script_mode = script_file.stat().st_mode
        assert script_mode & stat.S_IEXEC
    
    @patch('subprocess.run')
    def test_run_fai_build_success(self, mock_subprocess, config_file):
        """Test successful FAI build execution."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        builder.load_and_validate_config()
        fai_config_dir = self.output_dir / "fai-config"
        fai_config_dir.mkdir(parents=True)
        
        iso_path = builder.run_fai_build(fai_config_dir)
        
        assert iso_path.suffix == ".iso"
        assert "ubuntu" in iso_path.name.lower()
        assert "dell" in iso_path.name.lower()  # Hardware vendor
        
        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "fai-cd" in call_args
        assert str(fai_config_dir) in call_args
        assert str(iso_path) in call_args
    
    @patch('subprocess.run')
    def test_run_fai_build_failure(self, mock_subprocess, config_file):
        """Test FAI build execution failure."""
        # Mock failed subprocess call
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "FAI build failed"
        mock_subprocess.return_value = mock_result
        
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        builder.load_and_validate_config()
        fai_config_dir = self.output_dir / "fai-config"
        fai_config_dir.mkdir(parents=True)
        
        with pytest.raises(Exception):
            builder.run_fai_build(fai_config_dir)
    
    @patch('src.downloaders.packages.PackageDownloader.download_packages')
    @patch('src.downloaders.scripts.ScriptDownloader.download_scripts')
    def test_build_config_only(self, mock_download_scripts, mock_download_packages, config_file):
        """Test build process with config generation only."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        # Mock downloads
        mock_download_packages.return_value = {}
        mock_download_scripts.return_value = {}
        
        # Run build with skip_fai=True
        result_path = builder.build(skip_fai=True)
        
        assert result_path == self.output_dir
        
        # Check that config files were generated
        user_data = self.output_dir / "user-data.yaml"
        fai_config = self.output_dir / "fai-config"
        first_boot = self.output_dir / "first-boot"
        
        assert user_data.exists()
        assert fai_config.exists()
        assert first_boot.exists()
    
    @patch('subprocess.run')
    @patch('src.downloaders.packages.PackageDownloader.download_packages')
    @patch('src.downloaders.scripts.ScriptDownloader.download_scripts')
    def test_full_build_process(self, mock_download_scripts, mock_download_packages, mock_subprocess, config_file):
        """Test complete build process."""
        # Mock successful operations
        mock_download_packages.return_value = {}
        mock_download_scripts.return_value = {}
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        # Run complete build
        iso_path = builder.build()
        
        assert iso_path.suffix == ".iso"
        assert "ubuntu" in iso_path.name.lower()
        
        # Verify all config files were generated
        user_data = self.output_dir / "user-data.yaml"
        fai_config = self.output_dir / "fai-config"
        first_boot = self.output_dir / "first-boot"
        
        assert user_data.exists()
        assert fai_config.exists()
        assert first_boot.exists()
        
        # Verify FAI was called
        mock_subprocess.assert_called_once()
    
    def test_build_with_skip_downloads(self, config_file):
        """Test build process skipping downloads."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        # This should not fail even if no cached files exist
        result_path = builder.build(skip_downloads=True, skip_fai=True)
        
        assert result_path == self.output_dir
        
        # Config files should still be generated
        user_data = self.output_dir / "user-data.yaml"
        assert user_data.exists()
    
    def test_cleanup_temp_files(self, config_file):
        """Test temporary file cleanup."""
        builder = FAIBuilder(
            config_path=config_file,
            output_dir=self.output_dir,
            cache_dir=self.cache_dir
        )
        
        # Should not raise any exceptions
        builder.cleanup_temp_files()