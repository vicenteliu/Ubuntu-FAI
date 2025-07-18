"""Ubuntu Autoinstall configuration generator using Jinja2 templates."""

import hashlib
import logging
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import TemplateError, TemplateNotFound

from ..config.models import BuildConfig

logger = logging.getLogger(__name__)


class AutoinstallGenerationError(Exception):
    """Exception raised when autoinstall generation fails."""
    pass


class AutoinstallGenerator:
    """Generator for Ubuntu Autoinstall user-data.yaml configuration."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the autoinstall generator.
        
        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            templates_dir = Path(__file__).parent.parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        
        if not self.templates_dir.exists():
            raise AutoinstallGenerationError(f"Templates directory not found: {self.templates_dir}")
        
        # Configure Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters
        self.env.filters.update({
            'password_hash': self._password_hash_filter,
            'generate_salt': self._generate_salt_filter,
            'to_yaml': self._to_yaml_filter,
            'network_interface': self._network_interface_filter
        })
        
        # Add custom functions  
        self.env.globals.update({
            'build_timestamp': self._get_build_timestamp,
            'random_string': self._generate_random_string
        })
    
    def generate_user_data(self, config: BuildConfig, 
                          output_path: Optional[Path] = None) -> str:
        """Generate Ubuntu Autoinstall user-data.yaml content.
        
        Args:
            config: Build configuration object
            output_path: Optional path to write the generated content
            
        Returns:
            Generated user-data.yaml content as string
            
        Raises:
            AutoinstallGenerationError: If generation fails
        """
        try:
            # Load the user-data template
            template = self.env.get_template('user-data.yaml.j2')
            
            # Prepare template context
            context = self._prepare_template_context(config)
            
            # Render the template
            content = template.render(**context)
            
            # Validate generated YAML
            self._validate_yaml_syntax(content)
            
            # Validate autoinstall schema
            self._validate_autoinstall_schema(content)
            
            # Write to file if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Generated user-data.yaml: {output_path}")
            
            return content
            
        except TemplateNotFound as e:
            raise AutoinstallGenerationError(f"Template not found: {e}")
        except TemplateError as e:
            raise AutoinstallGenerationError(f"Template rendering error: {e}")
        except Exception as e:
            raise AutoinstallGenerationError(f"Failed to generate autoinstall config: {e}")
    
    def generate_first_boot_service(self, config: BuildConfig,
                                   output_path: Optional[Path] = None) -> str:
        """Generate systemd service for first-boot scripts.
        
        Args:
            config: Build configuration object
            output_path: Optional path to write the generated content
            
        Returns:
            Generated service file content as string
        """
        try:
            template = self.env.get_template('first-boot.service.j2')
            context = self._prepare_template_context(config)
            content = template.render(**context)
            
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Generated first-boot service: {output_path}")
            
            return content
            
        except Exception as e:
            raise AutoinstallGenerationError(f"Failed to generate first-boot service: {e}")
    
    def _prepare_template_context(self, config: BuildConfig) -> Dict[str, Any]:
        """Prepare template rendering context.
        
        Args:
            config: Build configuration object
            
        Returns:
            Template context dictionary
        """
        # Detect network interface
        network_interface = self._detect_network_interface(config)
        
        # Prepare timezone
        timezone = self._get_timezone(config)
        
        context = {
            'config': config,
            'network_interface': network_interface,
            'timezone': timezone,
            'build_timestamp': self._get_build_timestamp(),
            'build_info': {
                'version': '1.0.0',
                'generator': 'Ubuntu FAI Build System',
                'ubuntu_version': '24.04'
            }
        }
        
        return context
    
    def _detect_network_interface(self, config: BuildConfig) -> str:
        """Detect appropriate network interface name.
        
        Args:
            config: Build configuration object
            
        Returns:
            Network interface name
        """
        # Use predictable interface names based on hardware vendor
        vendor_interfaces = {
            'dell': 'eno1',
            'lenovo': 'enp0s31f6', 
            'hp': 'ens160',
            'generic': 'eth0'
        }
        
        return vendor_interfaces.get(config.hardware.vendor.value, 'eth0')
    
    def _get_timezone(self, config: BuildConfig) -> str:
        """Get timezone for the system.
        
        Args:
            config: Build configuration object
            
        Returns:
            Timezone string
        """
        # Default timezone - could be made configurable in the future
        return 'UTC'
    
    def _get_build_timestamp(self) -> str:
        """Get current build timestamp in ISO format.
        
        Returns:
            ISO format timestamp string
        """
        return datetime.now(timezone.utc).isoformat()
    
    def _generate_random_string(self, length: int = 16) -> str:
        """Generate a random string for use in templates.
        
        Args:
            length: Length of random string to generate
            
        Returns:
            Random string
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _password_hash_filter(self, password: str) -> str:
        """Jinja2 filter to hash passwords for user-data.yaml.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password in format suitable for Ubuntu autoinstall
        """
        # Generate salt
        salt = self._generate_salt()
        
        # Create SHA-512 hash with salt
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hashed = hashlib.pbkdf2_hmac('sha512', password_bytes, salt_bytes, 100000)
        hashed_hex = hashed.hex()
        
        # Return in crypt format
        return f"$6${salt}${hashed_hex}"
    
    def _generate_salt_filter(self, length: int = 16) -> str:
        """Jinja2 filter to generate salt for password hashing.
        
        Args:
            length: Length of salt to generate
            
        Returns:
            Random salt string
        """
        return self._generate_salt(length)
    
    def _generate_salt(self, length: int = 16) -> str:
        """Generate a random salt for password hashing.
        
        Args:
            length: Length of salt to generate
            
        Returns:
            Random salt string
        """
        alphabet = string.ascii_letters + string.digits + './'
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _to_yaml_filter(self, obj: Any) -> str:
        """Jinja2 filter to convert objects to YAML format.
        
        Args:
            obj: Object to convert to YAML
            
        Returns:
            YAML string representation
        """
        return yaml.dump(obj, default_flow_style=False, allow_unicode=True)
    
    def _network_interface_filter(self, vendor: str) -> str:
        """Jinja2 filter to get network interface name by vendor.
        
        Args:
            vendor: Hardware vendor name
            
        Returns:
            Network interface name
        """
        return self._detect_network_interface_by_vendor(vendor)
    
    def _detect_network_interface_by_vendor(self, vendor: str) -> str:
        """Detect network interface by hardware vendor.
        
        Args:
            vendor: Hardware vendor name
            
        Returns:
            Network interface name
        """
        vendor_interfaces = {
            'dell': 'eno1',
            'lenovo': 'enp0s31f6',
            'hp': 'ens160', 
            'generic': 'eth0'
        }
        
        return vendor_interfaces.get(vendor.lower(), 'eth0')
    
    def _validate_yaml_syntax(self, content: str) -> None:
        """Validate YAML syntax.
        
        Args:
            content: YAML content to validate
            
        Raises:
            AutoinstallGenerationError: If YAML syntax is invalid
        """
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise AutoinstallGenerationError(f"Invalid YAML syntax: {e}")
    
    def _validate_autoinstall_schema(self, content: str) -> None:
        """Validate autoinstall configuration schema.
        
        Args:
            content: Autoinstall YAML content to validate
            
        Raises:
            AutoinstallGenerationError: If schema validation fails
        """
        try:
            data = yaml.safe_load(content)
            
            # Basic schema validation
            if not isinstance(data, dict):
                raise AutoinstallGenerationError("Autoinstall config must be a dictionary")
            
            if 'autoinstall' not in data:
                raise AutoinstallGenerationError("Missing required 'autoinstall' key")
            
            autoinstall = data['autoinstall']
            if not isinstance(autoinstall, dict):
                raise AutoinstallGenerationError("'autoinstall' must be a dictionary")
            
            # Check required sections
            required_sections = ['version', 'identity', 'storage', 'locale']
            for section in required_sections:
                if section not in autoinstall:
                    logger.warning(f"Missing recommended section: {section}")
            
            # Validate version
            if 'version' in autoinstall:
                version = autoinstall['version']
                if version != 1:
                    raise AutoinstallGenerationError(f"Unsupported autoinstall version: {version}")
            
            logger.info("Autoinstall schema validation passed")
            
        except yaml.YAMLError as e:
            raise AutoinstallGenerationError(f"YAML parsing error during validation: {e}")
        except Exception as e:
            raise AutoinstallGenerationError(f"Schema validation error: {e}")


def generate_autoinstall_config(config: BuildConfig, 
                               output_dir: Optional[Path] = None) -> Dict[str, str]:
    """Convenience function to generate autoinstall configuration files.
    
    Args:
        config: Build configuration object
        output_dir: Directory to write generated files
        
    Returns:
        Dictionary mapping file types to generated content
        
    Raises:
        AutoinstallGenerationError: If generation fails
    """
    generator = AutoinstallGenerator()
    
    results = {}
    
    # Generate user-data.yaml
    user_data_path = None
    if output_dir:
        user_data_path = Path(output_dir) / "user-data.yaml"
    
    results['user-data'] = generator.generate_user_data(config, user_data_path)
    
    # Generate first-boot service if needed
    if config.first_boot.enabled and config.first_boot.scripts:
        service_path = None
        if output_dir:
            service_path = Path(output_dir) / "fai-first-boot.service"
        
        results['first-boot-service'] = generator.generate_first_boot_service(config, service_path)
    
    return results