"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from src.config.models import (
    BuildConfig, HardwareConfig, EncryptionConfig,
    PackageConfig, UserConfig, FirstBootConfig, NetworkConfig
)


class TestHardwareConfig:
    """Test hardware configuration model."""
    
    def test_valid_hardware_config(self, sample_hardware_config):
        """Test valid hardware configuration."""
        assert sample_hardware_config.vendor == "Dell"
        assert sample_hardware_config.model == "OptiPlex 7090"
        assert sample_hardware_config.cpu_cores == 8
        assert sample_hardware_config.memory_gb == 16
        assert sample_hardware_config.storage_gb == 512
    
    def test_invalid_vendor(self):
        """Test invalid vendor validation."""
        with pytest.raises(ValidationError):
            HardwareConfig(
                vendor="",  # Empty vendor
                model="Test Model",
                cpu_cores=4,
                memory_gb=8,
                storage_gb=256
            )
    
    def test_invalid_cpu_cores(self):
        """Test invalid CPU cores validation."""
        with pytest.raises(ValidationError):
            HardwareConfig(
                vendor="Dell",
                model="Test Model",
                cpu_cores=0,  # Invalid: zero cores
                memory_gb=8,
                storage_gb=256
            )
    
    def test_invalid_memory(self):
        """Test invalid memory validation."""
        with pytest.raises(ValidationError):
            HardwareConfig(
                vendor="Dell",
                model="Test Model",
                cpu_cores=4,
                memory_gb=0,  # Invalid: zero memory
                storage_gb=256
            )


class TestEncryptionConfig:
    """Test encryption configuration model."""
    
    def test_valid_encryption_config(self, sample_encryption_config):
        """Test valid encryption configuration."""
        assert sample_encryption_config.enabled is True
        assert sample_encryption_config.algorithm == "aes-xts-plain64"
        assert sample_encryption_config.key_size == 512
        assert sample_encryption_config.hash_algorithm == "sha256"
    
    def test_invalid_algorithm(self):
        """Test invalid encryption algorithm."""
        with pytest.raises(ValidationError):
            EncryptionConfig(
                enabled=True,
                algorithm="invalid-algorithm",
                key_size=512,
                hash_algorithm="sha256"
            )
    
    def test_invalid_key_size(self):
        """Test invalid key size."""
        with pytest.raises(ValidationError):
            EncryptionConfig(
                enabled=True,
                algorithm="aes-xts-plain64",
                key_size=64,  # Too small
                hash_algorithm="sha256"
            )
    
    def test_disabled_encryption(self):
        """Test disabled encryption configuration."""
        config = EncryptionConfig(
            enabled=False,
            algorithm="aes-xts-plain64",
            key_size=512,
            hash_algorithm="sha256"
        )
        assert config.enabled is False


class TestUserConfig:
    """Test user configuration model."""
    
    def test_valid_user_config(self, sample_user_config):
        """Test valid user configuration."""
        assert sample_user_config.username == "testuser"
        assert sample_user_config.full_name == "Test User"
        assert sample_user_config.create_user is True
        assert "sudo" in sample_user_config.groups
    
    def test_invalid_username(self):
        """Test invalid username validation."""
        with pytest.raises(ValidationError):
            UserConfig(
                username="root",  # Reserved username
                full_name="Root User",
                password_hash="$6$rounds=4096$salt$hash",
                create_user=True,
                auto_login=False,
                groups=["sudo"]
            )
    
    def test_invalid_password_hash(self):
        """Test invalid password hash validation."""
        with pytest.raises(ValidationError):
            UserConfig(
                username="testuser",
                full_name="Test User",
                password_hash="plaintext",  # Not a hash
                create_user=True,
                auto_login=False,
                groups=["sudo"]
            )
    
    def test_empty_groups(self):
        """Test user with no groups."""
        config = UserConfig(
            username="testuser",
            full_name="Test User",
            password_hash="$6$rounds=4096$salt$hash",
            create_user=True,
            auto_login=False,
            groups=[]
        )
        assert len(config.groups) == 0


class TestPackageConfig:
    """Test package configuration model."""
    
    def test_valid_package_config(self, sample_package_config):
        """Test valid package configuration."""
        assert len(sample_package_config.apt_packages) == 2
        assert len(sample_package_config.snap_packages) == 1
        assert len(sample_package_config.custom_debs) == 0
    
    def test_empty_package_config(self):
        """Test empty package configuration."""
        config = PackageConfig(
            apt_packages=[],
            snap_packages=[],
            custom_debs=[]
        )
        assert len(config.apt_packages) == 0
        assert len(config.snap_packages) == 0
        assert len(config.custom_debs) == 0


class TestBuildConfig:
    """Test complete build configuration model."""
    
    def test_valid_build_config(self, sample_build_config):
        """Test valid complete build configuration."""
        assert isinstance(sample_build_config.hardware, HardwareConfig)
        assert isinstance(sample_build_config.encryption, EncryptionConfig)
        assert isinstance(sample_build_config.packages, PackageConfig)
        assert isinstance(sample_build_config.user, UserConfig)
        assert isinstance(sample_build_config.first_boot, FirstBootConfig)
        assert isinstance(sample_build_config.network, NetworkConfig)
    
    def test_build_config_from_dict(self, sample_config_dict):
        """Test building configuration from dictionary."""
        config = BuildConfig(**sample_config_dict)
        assert config.hardware.vendor == "Dell"
        assert config.user.username == "testuser"
        assert config.encryption.enabled is True
    
    def test_invalid_build_config(self, invalid_config_dict):
        """Test invalid build configuration validation."""
        with pytest.raises(ValidationError):
            BuildConfig(**invalid_config_dict)
    
    def test_build_config_serialization(self, sample_build_config):
        """Test configuration serialization."""
        # Test model_dump (Pydantic v2)
        config_dict = sample_build_config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["hardware"]["vendor"] == "Dell"
        
        # Test round-trip
        new_config = BuildConfig(**config_dict)
        assert new_config.hardware.vendor == sample_build_config.hardware.vendor