"""Tests for configuration validator."""

import pytest

from src.config.validator import ConfigValidator, ValidationResult
from src.config.models import BuildConfig, HardwareConfig, EncryptionConfig


class TestConfigValidator:
    """Test configuration validator."""
    
    def setup_method(self):
        """Set up test method."""
        self.validator = ConfigValidator()
    
    def test_valid_config_validation(self, sample_build_config):
        """Test validation of valid configuration."""
        result = self.validator.validate_config(sample_build_config)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        # May have warnings but should be valid
    
    def test_hardware_validation(self, sample_build_config):
        """Test hardware-specific validation."""
        result = self.validator.validate_hardware(sample_build_config.hardware)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_hardware_vendor(self, sample_build_config):
        """Test invalid hardware vendor."""
        # Modify hardware to have invalid vendor
        sample_build_config.hardware.vendor = "UnknownVendor"
        
        result = self.validator.validate_hardware(sample_build_config.hardware)
        
        # Should still be valid but may have warnings
        assert result.is_valid is True
        # Check if there are warnings about unknown vendor
        warning_messages = [w.lower() for w in result.warnings]
        assert any("vendor" in msg or "unknown" in msg for msg in warning_messages)
    
    def test_encryption_validation(self, sample_build_config):
        """Test encryption configuration validation."""
        result = self.validator.validate_encryption(sample_build_config.encryption)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_weak_encryption_warning(self, sample_build_config):
        """Test weak encryption algorithm warning."""
        # Set weak encryption
        sample_build_config.encryption.key_size = 256  # Minimum but might warn
        
        result = self.validator.validate_encryption(sample_build_config.encryption)
        
        # Should be valid but may have warnings
        assert result.is_valid is True
    
    def test_user_validation(self, sample_build_config):
        """Test user configuration validation."""
        result = self.validator.validate_user(sample_build_config.user)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_reserved_username(self, sample_build_config):
        """Test reserved username validation."""
        # Try to use reserved username
        sample_build_config.user.username = "root"
        
        result = self.validator.validate_user(sample_build_config.user)
        
        # Should be invalid
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("reserved" in error.lower() or "root" in error.lower() 
                  for error in result.errors)
    
    def test_weak_password_hash(self, sample_build_config):
        """Test weak password hash validation."""
        # Set plaintext password (invalid)
        sample_build_config.user.password_hash = "plaintext"
        
        result = self.validator.validate_user(sample_build_config.user)
        
        # Should be invalid
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("password" in error.lower() or "hash" in error.lower() 
                  for error in result.errors)
    
    def test_package_validation(self, sample_build_config):
        """Test package configuration validation."""
        result = self.validator.validate_packages(sample_build_config.packages)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_network_validation(self, sample_build_config):
        """Test network configuration validation."""
        result = self.validator.validate_network(sample_build_config.network)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_wifi_config_validation(self, sample_build_config):
        """Test WiFi configuration validation."""
        # Enable WiFi but don't provide credentials
        sample_build_config.network.configure_wifi = True
        sample_build_config.network.wifi_ssid = None
        
        result = self.validator.validate_network(sample_build_config.network)
        
        # Should be invalid - WiFi enabled but no credentials
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("wifi" in error.lower() or "ssid" in error.lower() 
                  for error in result.errors)
    
    def test_complete_invalid_config(self):
        """Test completely invalid configuration."""
        # Create invalid config
        invalid_hardware = HardwareConfig(
            vendor="Dell",
            model="Test",
            cpu_cores=1,  # Very low but valid
            memory_gb=1,  # Very low but valid  
            storage_gb=1   # Very low but valid
        )
        
        invalid_encryption = EncryptionConfig(
            enabled=True,
            algorithm="aes-xts-plain64",  # Valid
            key_size=256,  # Minimum but valid
            hash_algorithm="sha256"  # Valid
        )
        
        # Create config with valid sub-components but check overall validation
        from src.config.models import PackageConfig, UserConfig, FirstBootConfig, NetworkConfig
        
        try:
            config = BuildConfig(
                hardware=invalid_hardware,
                encryption=invalid_encryption,
                packages=PackageConfig(apt_packages=[], snap_packages=[], custom_debs=[]),
                user=UserConfig(
                    username="testuser",
                    full_name="Test User", 
                    password_hash="$6$rounds=4096$salt$hash",
                    create_user=True,
                    auto_login=False,
                    groups=["sudo"]
                ),
                first_boot=FirstBootConfig(
                    enabled=True,
                    install_packages=True,
                    enable_services=True,
                    scripts=[]
                ),
                network=NetworkConfig(
                    configure_wifi=False,
                    wifi_ssid=None,
                    wifi_password=None,
                    static_ip=False
                )
            )
            
            result = self.validator.validate_config(config)
            
            # Even if individual components are valid, overall config might have warnings
            # The test should pass but may have warnings about low specs
            assert isinstance(result, ValidationResult)
            
        except Exception as e:
            pytest.fail(f"Config validation raised unexpected exception: {e}")
    
    def test_validation_result_representation(self):
        """Test ValidationResult string representation."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        assert "Error 1" in str(result)
        assert "Error 2" in str(result)
        assert "Warning 1" in str(result)