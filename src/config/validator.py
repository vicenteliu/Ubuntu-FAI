"""Configuration validation and loading utilities for Ubuntu FAI build system."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from .models import BuildConfig, HardwareVendor, ScriptType

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of configuration validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        """Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __str__(self) -> str:
        """String representation of validation result."""
        result = f"Validation: {'PASSED' if self.is_valid else 'FAILED'}"
        if self.errors:
            result += f"\nErrors:\n" + "\n".join(f"  - {error}" for error in self.errors)
        if self.warnings:
            result += f"\nWarnings:\n" + "\n".join(f"  - {warning}" for warning in self.warnings)
        return result


class ConfigValidator:
    """Configuration validator for Ubuntu FAI build system."""
    
    def __init__(self):
        """Initialize config validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_config(self, config: BuildConfig) -> ValidationResult:
        """Validate complete build configuration.
        
        Args:
            config: Build configuration to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        # Validate individual components
        hardware_result = self.validate_hardware(config.hardware)
        errors.extend(hardware_result.errors)
        warnings.extend(hardware_result.warnings)
        
        encryption_result = self.validate_encryption(config.encryption)
        errors.extend(encryption_result.errors)
        warnings.extend(encryption_result.warnings)
        
        user_result = self.validate_user(config.user)
        errors.extend(user_result.errors)
        warnings.extend(user_result.warnings)
        
        packages_result = self.validate_packages(config.packages)
        errors.extend(packages_result.errors)
        warnings.extend(packages_result.warnings)
        
        network_result = self.validate_network(config.network)
        errors.extend(network_result.errors)
        warnings.extend(network_result.warnings)
        
        # Cross-component validation
        try:
            _validate_hardware_encryption_compatibility(config)
            _validate_first_boot_scripts(config)
            _validate_package_dependencies(config)
        except ConfigValidationError as e:
            errors.append(str(e))
        
        # Add recommendations as warnings
        recommendations = validate_config_completeness(config)
        warnings.extend(recommendations)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)
    
    def validate_hardware(self, hardware) -> ValidationResult:
        """Validate hardware configuration.
        
        Args:
            hardware: Hardware configuration
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Check vendor
        if hasattr(hardware, 'vendor') and hardware.vendor:
            vendor_lower = hardware.vendor.lower()
            if vendor_lower not in ['dell', 'lenovo', 'hp', 'generic']:
                warnings.append(f"Unknown hardware vendor: {hardware.vendor}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_encryption(self, encryption) -> ValidationResult:
        """Validate encryption configuration.
        
        Args:
            encryption: Encryption configuration
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if encryption.enabled:
            # Check cipher
            valid_ciphers = ['aes-xts-plain64', 'aes-cbc-essiv:sha256', 'serpent-xts-plain64']
            if encryption.cipher not in valid_ciphers:
                errors.append(f"Invalid encryption cipher: {encryption.cipher}")
            
            # Check key size
            if encryption.key_size < 256:
                errors.append(f"Encryption key size too small: {encryption.key_size} (minimum: 256)")
            elif encryption.key_size == 256:
                warnings.append("Consider using key size 512 for stronger encryption")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_user(self, user) -> ValidationResult:
        """Validate user configuration.
        
        Args:
            user: User configuration
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Check reserved usernames
        reserved_usernames = ['root', 'admin', 'administrator', 'sys', 'system']
        if user.username.lower() in reserved_usernames:
            errors.append(f"Reserved username not allowed: {user.username}")
        
        # Check password hash format
        if hasattr(user, 'password_hash') and user.password_hash:
            if not user.password_hash.startswith('$'):
                errors.append("Password hash must be properly hashed (should start with $)")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_packages(self, packages) -> ValidationResult:
        """Validate package configuration.
        
        Args:
            packages: Package configuration
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Basic validation - most package validation is done elsewhere
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def validate_network(self, network) -> ValidationResult:
        """Validate network configuration.
        
        Args:
            network: Network configuration
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # WiFi validation
        if hasattr(network, 'configure_wifi') and network.configure_wifi:
            if not hasattr(network, 'wifi_ssid') or not network.wifi_ssid:
                errors.append("WiFi enabled but no SSID provided")
            if not hasattr(network, 'wifi_password') or not network.wifi_password:
                errors.append("WiFi enabled but no password provided")
        
        return ValidationResult(len(errors) == 0, errors, warnings)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


def load_config_from_file(config_path: Path) -> BuildConfig:
    """Load and validate configuration from JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        Validated BuildConfig instance
        
    Raises:
        ConfigValidationError: If file cannot be read or configuration is invalid
        FileNotFoundError: If configuration file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    if not config_path.is_file():
        raise ConfigValidationError(f"Path is not a file: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to read configuration file: {e}")
    
    return validate_config_dict(config_data)


def validate_config_dict(config_data: Dict[str, Any]) -> BuildConfig:
    """Validate configuration dictionary and return BuildConfig instance.
    
    Args:
        config_data: Dictionary containing configuration data
        
    Returns:
        Validated BuildConfig instance
        
    Raises:
        ConfigValidationError: If configuration is invalid
    """
    try:
        config = BuildConfig.model_validate(config_data)
        
        # Additional custom validation
        _validate_package_dependencies(config)
        _validate_hardware_encryption_compatibility(config)
        _validate_first_boot_scripts(config)
        
        return config
        
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        error_messages = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field_path}: {message}")
        
        raise ConfigValidationError(
            f"Configuration validation failed:\n" + "\n".join(f"  - {msg}" for msg in error_messages),
            errors=e.errors()
        )


def _validate_package_dependencies(config: BuildConfig) -> None:
    """Validate package dependencies and conflicts.
    
    Args:
        config: BuildConfig instance to validate
        
    Raises:
        ConfigValidationError: If package dependencies are invalid
    """
    # Check for conflicting packages
    conflicting_packages = {
        'firefox': ['chromium-browser', 'google-chrome-stable'],
        'vim': ['nano'],
        'apache2': ['nginx'],
        'mysql-server': ['postgresql']
    }
    
    installed_packages = set(config.packages.apt_packages)
    
    for package, conflicts in conflicting_packages.items():
        if package in installed_packages:
            for conflict in conflicts:
                if conflict in installed_packages:
                    raise ConfigValidationError(
                        f"Conflicting packages detected: {package} and {conflict} cannot be installed together"
                    )
    
    # Validate essential packages for desktop installation
    if config.hardware.vendor != HardwareVendor.GENERIC:
        essential_packages = ['ubuntu-desktop', 'gdm3']
        missing_essential = []
        
        for package in essential_packages:
            if package not in installed_packages:
                missing_essential.append(package)
        
        if missing_essential:
            logger.warning(
                f"Essential desktop packages not explicitly listed: {', '.join(missing_essential)}. "
                "These will be installed via FAI class configuration."
            )


def _validate_hardware_encryption_compatibility(config: BuildConfig) -> None:
    """Validate hardware-specific encryption compatibility.
    
    Args:
        config: BuildConfig instance to validate
        
    Raises:
        ConfigValidationError: If hardware and encryption settings are incompatible
    """
    if not config.encryption.enabled:
        return
    
    # Dell-specific validation
    if config.hardware.vendor == HardwareVendor.DELL:
        if config.encryption.key_size > 256:
            logger.warning(
                "Dell hardware may have compatibility issues with LUKS key sizes > 256 bits. "
                "Consider using key_size: 256 for better compatibility."
            )
        
        if config.encryption.cipher not in ['aes-xts-plain64', 'aes-cbc-essiv:sha256']:
            logger.warning(
                f"Cipher '{config.encryption.cipher}' may not be optimal for Dell hardware. "
                "Consider using 'aes-xts-plain64' for better performance."
            )
    
    # Lenovo-specific validation
    if config.hardware.vendor == HardwareVendor.LENOVO:
        if config.hardware.target_ssd and config.encryption.enabled:
            logger.info(
                "Lenovo systems with SSD and encryption enabled may require "
                "additional firmware settings for optimal performance."
            )
    
    # HP-specific validation
    if config.hardware.vendor == HardwareVendor.HP:
        if config.encryption.cipher == 'serpent-xts-plain64':
            logger.warning(
                "Serpent cipher may have performance issues on HP hardware. "
                "Consider using AES-based ciphers for better performance."
            )


def _validate_first_boot_scripts(config: BuildConfig) -> None:
    """Validate first-boot script configuration.
    
    Args:
        config: BuildConfig instance to validate
        
    Raises:
        ConfigValidationError: If first-boot script configuration is invalid
    """
    if not config.first_boot.enabled or not config.first_boot.scripts:
        return
    
    # Validate script ordering
    automated_scripts = [s for s in config.first_boot.scripts if s.type == ScriptType.AUTOMATED]
    manual_scripts = [s for s in config.first_boot.scripts if s.type == ScriptType.MANUAL]
    
    if manual_scripts and automated_scripts:
        # Check if manual scripts come after automated ones
        for i, script in enumerate(config.first_boot.scripts):
            if script.type == ScriptType.MANUAL:
                # Ensure no automated scripts come after this manual script
                remaining_scripts = config.first_boot.scripts[i+1:]
                if any(s.type == ScriptType.AUTOMATED for s in remaining_scripts):
                    raise ConfigValidationError(
                        "Automated scripts cannot be scheduled after manual scripts. "
                        "Please reorder scripts to have all automated scripts before manual ones."
                    )
                break
    
    # Validate script URLs and paths uniqueness
    script_identifiers = []
    for script in config.first_boot.scripts:
        if script.url:
            script_identifiers.append(('url', script.url))
        elif script.local_path:
            script_identifiers.append(('local_path', script.local_path))
    
    if len(script_identifiers) != len(set(script_identifiers)):
        raise ConfigValidationError("Duplicate script URLs/paths detected in first_boot configuration")
    
    # Validate timeout for script count
    script_count = len(config.first_boot.scripts)
    min_timeout = script_count * 60  # Minimum 1 minute per script
    
    if config.first_boot.timeout_seconds < min_timeout:
        logger.warning(
            f"First-boot timeout ({config.first_boot.timeout_seconds}s) may be too short "
            f"for {script_count} scripts. Consider at least {min_timeout}s."
        )


def validate_config_completeness(config: BuildConfig) -> List[str]:
    """Check configuration completeness and return list of recommendations.
    
    Args:
        config: BuildConfig instance to check
        
    Returns:
        List of recommendation messages
    """
    recommendations = []
    
    # Check user configuration
    if not config.user.ssh_authorized_keys and not config.user.password:
        recommendations.append(
            "No SSH keys or password configured for user. "
            "Consider adding SSH keys for secure access."
        )
    
    if config.user.sudo_nopasswd and not config.user.ssh_authorized_keys:
        recommendations.append(
            "Passwordless sudo enabled without SSH keys. "
            "This may create a security risk if password authentication is used."
        )
    
    # Check encryption configuration
    if not config.encryption.enabled:
        recommendations.append(
            "Disk encryption is disabled. "
            "Consider enabling LUKS encryption for better security."
        )
    
    # Check package configuration
    if not config.packages.apt_packages and not config.packages.deb_urls:
        recommendations.append(
            "No custom packages specified. "
            "The system will be installed with default Ubuntu Desktop packages only."
        )
    
    # Check first-boot configuration
    if config.first_boot.enabled and not config.first_boot.scripts:
        recommendations.append(
            "First-boot execution is enabled but no scripts specified. "
            "Consider disabling first-boot or adding scripts."
        )
    
    return recommendations


def get_config_summary(config: BuildConfig) -> Dict[str, Any]:
    """Generate a summary of the configuration for display purposes.
    
    Args:
        config: BuildConfig instance to summarize
        
    Returns:
        Dictionary containing configuration summary
    """
    return {
        "hardware": {
            "vendor": config.hardware.vendor.value,
            "target_ssd": config.hardware.target_ssd,
            "disk_size_min_gb": config.hardware.disk_size_min_gb
        },
        "encryption": {
            "enabled": config.encryption.enabled,
            "cipher": config.encryption.cipher if config.encryption.enabled else None,
            "key_size": config.encryption.key_size if config.encryption.enabled else None
        },
        "packages": {
            "apt_packages_count": len(config.packages.apt_packages),
            "deb_urls_count": len(config.packages.deb_urls),
            "snap_packages_count": len(config.packages.snap_packages)
        },
        "user": {
            "username": config.user.username,
            "has_password": bool(config.user.password),
            "ssh_keys_count": len(config.user.ssh_authorized_keys),
            "sudo_nopasswd": config.user.sudo_nopasswd
        },
        "first_boot": {
            "enabled": config.first_boot.enabled,
            "scripts_count": len(config.first_boot.scripts),
            "timeout_seconds": config.first_boot.timeout_seconds
        },
        "network": {
            "dhcp": config.network.dhcp,
            "hostname": config.network.hostname
        },
        "build": {
            "iso_label": config.iso_label,
            "iso_filename": config.get_iso_filename(),
            "fai_classes": config.get_fai_classes()
        }
    }