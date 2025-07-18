"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest

from src.config.models import (
    BuildConfig, HardwareConfig, EncryptionConfig, 
    PackageConfig, UserConfig, FirstBootConfig, NetworkConfig
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_hardware_config() -> HardwareConfig:
    """Sample hardware configuration."""
    return HardwareConfig(
        vendor="Dell",
        model="OptiPlex 7090",
        cpu_cores=8,
        memory_gb=16,
        storage_gb=512
    )


@pytest.fixture
def sample_encryption_config() -> EncryptionConfig:
    """Sample encryption configuration."""
    return EncryptionConfig(
        enabled=True,
        algorithm="aes-xts-plain64",
        key_size=512,
        hash_algorithm="sha256"
    )


@pytest.fixture
def sample_package_config() -> PackageConfig:
    """Sample package configuration."""
    return PackageConfig(
        apt_packages=[
            {"name": "git", "version": "latest"},
            {"name": "curl", "version": "latest"}
        ],
        snap_packages=[
            {"name": "code", "classic": True}
        ],
        custom_debs=[]
    )


@pytest.fixture
def sample_user_config() -> UserConfig:
    """Sample user configuration."""
    return UserConfig(
        username="testuser",
        full_name="Test User",
        password_hash="$6$rounds=4096$salt$hash",
        create_user=True,
        auto_login=False,
        groups=["sudo", "users"]
    )


@pytest.fixture
def sample_first_boot_config() -> FirstBootConfig:
    """Sample first boot configuration."""
    return FirstBootConfig(
        enabled=True,
        install_packages=True,
        enable_services=True,
        scripts=[]
    )


@pytest.fixture
def sample_network_config() -> NetworkConfig:
    """Sample network configuration."""
    return NetworkConfig(
        configure_wifi=False,
        wifi_ssid=None,
        wifi_password=None,
        static_ip=False
    )


@pytest.fixture
def sample_build_config(
    sample_hardware_config,
    sample_encryption_config,
    sample_package_config,
    sample_user_config,
    sample_first_boot_config,
    sample_network_config
) -> BuildConfig:
    """Sample complete build configuration."""
    return BuildConfig(
        hardware=sample_hardware_config,
        encryption=sample_encryption_config,
        packages=sample_package_config,
        user=sample_user_config,
        first_boot=sample_first_boot_config,
        network=sample_network_config
    )


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Sample configuration as dictionary."""
    return {
        "hardware": {
            "vendor": "Dell",
            "model": "OptiPlex 7090",
            "cpu_cores": 8,
            "memory_gb": 16,
            "storage_gb": 512
        },
        "encryption": {
            "enabled": True,
            "algorithm": "aes-xts-plain64",
            "key_size": 512,
            "hash_algorithm": "sha256"
        },
        "packages": {
            "apt_packages": [
                {"name": "git", "version": "latest"},
                {"name": "curl", "version": "latest"}
            ],
            "snap_packages": [
                {"name": "code", "classic": True}
            ],
            "custom_debs": []
        },
        "user": {
            "username": "testuser",
            "full_name": "Test User",
            "password_hash": "$6$rounds=4096$salt$hash",
            "create_user": True,
            "auto_login": False,
            "groups": ["sudo", "users"]
        },
        "first_boot": {
            "enabled": True,
            "install_packages": True,
            "enable_services": True,
            "scripts": []
        },
        "network": {
            "configure_wifi": False,
            "wifi_ssid": None,
            "wifi_password": None,
            "static_ip": False
        }
    }


@pytest.fixture
def config_file(temp_dir, sample_config_dict) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(sample_config_dict, f, indent=2)
    return config_path


@pytest.fixture
def invalid_config_dict() -> Dict[str, Any]:
    """Invalid configuration for testing validation."""
    return {
        "hardware": {
            "vendor": "",  # Invalid: empty vendor
            "model": "Test Model",
            "cpu_cores": -1,  # Invalid: negative cores
            "memory_gb": 16,
            "storage_gb": 512
        },
        "encryption": {
            "enabled": True,
            "algorithm": "invalid-algorithm",  # Invalid algorithm
            "key_size": 128,  # Invalid: too small
            "hash_algorithm": "md5"  # Invalid: weak hash
        },
        "packages": {
            "apt_packages": [],
            "snap_packages": [],
            "custom_debs": []
        },
        "user": {
            "username": "root",  # Invalid: root user
            "full_name": "Root User",
            "password_hash": "plain-password",  # Invalid: not hashed
            "create_user": True,
            "auto_login": False,
            "groups": []
        },
        "first_boot": {
            "enabled": True,
            "install_packages": True,
            "enable_services": True,
            "scripts": []
        },
        "network": {
            "configure_wifi": False,
            "wifi_ssid": None,
            "wifi_password": None,
            "static_ip": False
        }
    }