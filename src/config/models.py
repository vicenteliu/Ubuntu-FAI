"""Pydantic v2 models for Ubuntu FAI build system configuration validation."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HardwareVendor(str, Enum):
    """Supported hardware vendors for FAI classes."""
    DELL = "dell"
    LENOVO = "lenovo"
    HP = "hp"
    GENERIC = "generic"


class ScriptType(str, Enum):
    """Types of first-boot scripts."""
    AUTOMATED = "automated"
    MANUAL = "manual"


class HardwareConfig(BaseModel):
    """Hardware-specific configuration settings."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    vendor: HardwareVendor = Field(
        default=HardwareVendor.GENERIC,
        description="Hardware vendor for FAI class selection"
    )
    target_ssd: bool = Field(
        default=True,
        description="Target SSD drives for installation"
    )
    disk_size_min_gb: Optional[int] = Field(
        default=None,
        ge=20,
        le=10000,
        description="Minimum disk size in GB (None for largest available)"
    )
    
    @field_validator('vendor')
    @classmethod
    def validate_vendor(cls, v: HardwareVendor) -> HardwareVendor:
        """Validate hardware vendor selection."""
        if v not in HardwareVendor:
            raise ValueError(f"Unsupported hardware vendor: {v}")
        return v


class EncryptionConfig(BaseModel):
    """LUKS full-disk encryption configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    enabled: bool = Field(
        default=True,
        description="Enable LUKS full-disk encryption"
    )
    passphrase: str = Field(
        min_length=12,
        max_length=1024,
        description="LUKS encryption passphrase (minimum 12 characters)"
    )
    cipher: str = Field(
        default="aes-xts-plain64",
        description="LUKS cipher specification"
    )
    key_size: int = Field(
        default=512,
        ge=256,
        le=512,
        description="LUKS key size in bits"
    )
    
    @field_validator('passphrase')
    @classmethod
    def validate_passphrase(cls, v: str) -> str:
        """Validate LUKS passphrase strength."""
        if len(v) < 12:
            raise ValueError("Passphrase must be at least 12 characters long")
        
        # Check for basic complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        complexity_score = sum([has_upper, has_lower, has_digit, has_special])
        if complexity_score < 3:
            raise ValueError(
                "Passphrase must contain at least 3 of: uppercase, lowercase, digits, special characters"
            )
        
        return v
    
    @field_validator('cipher')
    @classmethod
    def validate_cipher(cls, v: str) -> str:
        """Validate LUKS cipher specification."""
        valid_ciphers = [
            "aes-xts-plain64",
            "aes-cbc-essiv:sha256",
            "aes-lrw-benbi",
            "serpent-xts-plain64",
            "twofish-xts-plain64"
        ]
        if v not in valid_ciphers:
            raise ValueError(f"Invalid cipher. Supported: {', '.join(valid_ciphers)}")
        return v


class PackageConfig(BaseModel):
    """Package installation configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    apt_packages: List[str] = Field(
        default_factory=list,
        description="APT packages to install from repositories"
    )
    deb_urls: List[str] = Field(
        default_factory=list,
        description="URLs to .deb packages for direct download"
    )
    deb_local_paths: List[str] = Field(
        default_factory=list,
        description="Local paths to .deb packages"
    )
    deb_target_dir: str = Field(
        default="/opt/packages",
        description="Directory where .deb files will be placed in target system"
    )
    snap_packages: List[str] = Field(
        default_factory=list,
        description="Snap packages to install"
    )
    
    @field_validator('apt_packages')
    @classmethod
    def validate_apt_packages(cls, v: List[str]) -> List[str]:
        """Validate APT package names."""
        for package in v:
            if not package or not package.replace('-', '').replace('.', '').replace('+', '').isalnum():
                raise ValueError(f"Invalid APT package name: {package}")
        return v
    
    @field_validator('deb_urls')
    @classmethod
    def validate_deb_urls(cls, v: List[str]) -> List[str]:
        """Validate .deb package URLs."""
        for url in v:
            try:
                parsed = urlparse(url)
                if not parsed.scheme in ('http', 'https'):
                    raise ValueError(f"Invalid URL scheme: {url}")
                if not parsed.netloc:
                    raise ValueError(f"Invalid URL format: {url}")
                # 允许重定向链接，不强制要求以 .deb 结尾
                # 实际的 .deb 文件验证将在下载时进行
                if url.endswith('.deb'):
                    # 直接 .deb 链接，验证通过
                    pass
                elif any(domain in parsed.netloc for domain in ['code.visualstudio.com', 'dl.google.com', 'github.com']):
                    # 已知的软件下载站点，允许重定向链接
                    pass
                else:
                    # 其他链接，警告但不阻止
                    import warnings
                    warnings.warn(f"URL may not point to .deb file, will verify during download: {url}")
            except Exception as e:
                raise ValueError(f"Invalid .deb URL {url}: {e}")
        return v
    
    @field_validator('deb_local_paths')
    @classmethod
    def validate_deb_local_paths(cls, v: List[str]) -> List[str]:
        """Validate local .deb package paths."""
        for path_str in v:
            path = Path(path_str)
            if not path.exists():
                raise ValueError(f"Local .deb file not found: {path_str}")
            if not path.is_file():
                raise ValueError(f"Local .deb path is not a file: {path_str}")
            if not path.suffix == '.deb':
                raise ValueError(f"File is not a .deb package: {path_str}")
        return v


class UserConfig(BaseModel):
    """User account configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    username: str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[a-z][a-z0-9_-]*$",
        description="Primary user account name"
    )
    full_name: str = Field(
        default="",
        max_length=128,
        description="User's full name"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        description="User password (will be hashed)"
    )
    ssh_authorized_keys: List[str] = Field(
        default_factory=list,
        description="SSH public keys for passwordless login"
    )
    sudo_nopasswd: bool = Field(
        default=False,
        description="Enable passwordless sudo for user"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v[0].islower():
            raise ValueError("Username must start with lowercase letter")
        if len(v) > 32:
            raise ValueError("Username cannot exceed 32 characters")
        return v
    
    @field_validator('ssh_authorized_keys')
    @classmethod
    def validate_ssh_keys(cls, v: List[str]) -> List[str]:
        """Validate SSH public key format."""
        for key in v:
            key_parts = key.strip().split()
            if len(key_parts) < 2:
                raise ValueError(f"Invalid SSH key format: {key[:50]}...")
            
            key_type = key_parts[0]
            if key_type not in ['ssh-rsa', 'ssh-ed25519', 'ssh-ecdsa']:
                raise ValueError(f"Unsupported SSH key type: {key_type}")
        
        return v


class FirstBootScript(BaseModel):
    """Individual first-boot script configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    url: Optional[str] = Field(
        default=None,
        description="URL to download the script from"
    )
    local_path: Optional[str] = Field(
        default=None,
        description="Local path to the script file"
    )
    type: ScriptType = Field(
        default=ScriptType.AUTOMATED,
        description="Script execution type (automated or manual)"
    )
    checksum: Optional[str] = Field(
        default=None,
        description="SHA256 checksum for script verification"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate script URL."""
        if v is None:
            return v
        try:
            parsed = urlparse(v)
            if not parsed.scheme in ('http', 'https'):
                raise ValueError(f"Invalid URL scheme: {v}")
            if not parsed.netloc:
                raise ValueError(f"Invalid URL format: {v}")
        except Exception as e:
            raise ValueError(f"Invalid script URL {v}: {e}")
        return v
    
    @field_validator('local_path')
    @classmethod
    def validate_local_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate local script path."""
        if v is None:
            return v
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Local script file not found: {v}")
        if not path.is_file():
            raise ValueError(f"Local script path is not a file: {v}")
        return v
    
    @field_validator('checksum')
    @classmethod
    def validate_checksum(cls, v: Optional[str]) -> Optional[str]:
        """Validate SHA256 checksum format."""
        if v is not None:
            if len(v) != 64 or not all(c in '0123456789abcdef' for c in v.lower()):
                raise ValueError("Checksum must be a valid 64-character SHA256 hash")
            return v.lower()
        return v
    
    @model_validator(mode='after')
    def validate_script_source(self) -> 'FirstBootScript':
        """Validate that script has either URL or local path."""
        if not self.url and not self.local_path:
            raise ValueError("Script must have either 'url' or 'local_path' specified")
        if self.url and self.local_path:
            raise ValueError("Script cannot have both 'url' and 'local_path' specified")
        return self


class FirstBootConfig(BaseModel):
    """First-boot script execution configuration."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    enabled: bool = Field(
        default=True,
        description="Enable first-boot script execution"
    )
    scripts: List[FirstBootScript] = Field(
        default_factory=list,
        description="List of first-boot scripts to execute"
    )
    timeout_seconds: int = Field(
        default=1800,
        ge=60,
        le=7200,
        description="Maximum execution time for all scripts"
    )
    scripts_target_dir: str = Field(
        default="/opt/scripts",
        description="Directory where scripts will be placed in target system"
    )


class NetworkConfig(BaseModel):
    """Network configuration settings."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )
    
    dhcp: bool = Field(
        default=True,
        description="Use DHCP for network configuration"
    )
    hostname: str = Field(
        default="ubuntu-fai",
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$",
        description="System hostname"
    )


class BuildConfig(BaseModel):
    """Main configuration model for Ubuntu FAI build system."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",
        validate_default=True
    )
    
    # Core configuration sections
    hardware: HardwareConfig = Field(
        default_factory=HardwareConfig,
        description="Hardware-specific configuration"
    )
    encryption: EncryptionConfig = Field(
        description="LUKS encryption configuration"
    )
    packages: PackageConfig = Field(
        default_factory=PackageConfig,
        description="Package installation configuration"
    )
    user: UserConfig = Field(
        description="Primary user account configuration"
    )
    first_boot: FirstBootConfig = Field(
        default_factory=FirstBootConfig,
        description="First-boot script configuration"
    )
    network: NetworkConfig = Field(
        default_factory=NetworkConfig,
        description="Network configuration"
    )
    
    # Build metadata
    iso_label: str = Field(
        default="Ubuntu-FAI",
        max_length=32,
        description="ISO volume label"
    )
    iso_filename: Optional[str] = Field(
        default=None,
        description="Custom ISO filename (auto-generated if None)"
    )
    
    # Base ISO configuration
    base_iso_path: Optional[str] = Field(
        default=None,
        description="Path to local Ubuntu base ISO file (optional)"
    )
    base_iso_url: Optional[str] = Field(
        default="http://releases.ubuntu.com/24.04/ubuntu-24.04.1-desktop-amd64.iso",
        description="URL to download Ubuntu base ISO (used if base_iso_path not specified)"
    )
    base_iso_checksum: Optional[str] = Field(
        default=None,
        description="SHA256 checksum of base ISO for verification"
    )
    
    @model_validator(mode='after')
    def validate_config_consistency(self) -> 'BuildConfig':
        """Validate cross-field configuration consistency."""
        # Encryption validation
        if self.encryption.enabled and not self.encryption.passphrase:
            raise ValueError("Encryption passphrase required when encryption is enabled")
        
        # User validation
        if not self.user.password and not self.user.ssh_authorized_keys:
            raise ValueError("User must have either password or SSH keys configured")
        
        # Hardware-specific encryption compatibility
        if self.hardware.vendor == HardwareVendor.DELL and self.encryption.enabled:
            # Dell-specific LUKS compatibility check
            if self.encryption.key_size > 256:
                raise ValueError("Dell hardware may have issues with key sizes > 256 bits")
        
        # Base ISO validation
        if self.base_iso_path:
            from pathlib import Path
            iso_path = Path(self.base_iso_path)
            if not iso_path.exists():
                raise ValueError(f"Base ISO file not found: {self.base_iso_path}")
            if not iso_path.is_file():
                raise ValueError(f"Base ISO path is not a file: {self.base_iso_path}")
            if iso_path.suffix.lower() != '.iso':
                raise ValueError(f"Base ISO file must have .iso extension: {self.base_iso_path}")
        
        return self
    
    def get_fai_classes(self) -> List[str]:
        """Generate FAI class list based on configuration."""
        classes = ["UBUNTU_DESKTOP"]
        
        # Hardware-specific class
        if self.hardware.vendor != HardwareVendor.GENERIC:
            classes.append(f"HARDWARE_{self.hardware.vendor.upper()}")
        
        # Encryption class
        if self.encryption.enabled:
            classes.append("UBUNTU_ENCRYPTED")
        
        # Custom software class
        if self.packages.apt_packages or self.packages.deb_urls:
            classes.append("CUSTOM_SOFTWARE")
        
        return classes
    
    def get_iso_filename(self) -> str:
        """Generate ISO filename based on configuration."""
        if self.iso_filename:
            return self.iso_filename
        
        # Auto-generate filename
        base = f"ubuntu-24.04-desktop-{self.hardware.vendor.value}"
        if self.encryption.enabled:
            base += "-encrypted"
        base += ".iso"
        
        return base