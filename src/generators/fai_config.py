"""FAI configuration space generator for Ubuntu FAI build system."""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, TemplateError

from ..config.models import BuildConfig

logger = logging.getLogger(__name__)


class FAIConfigGenerationError(Exception):
    """Exception raised when FAI configuration generation fails."""
    pass


class FAIConfigGenerator:
    """Generator for FAI configuration space with dynamic customization."""
    
    def __init__(self, 
                 base_config_dir: Optional[Path] = None,
                 templates_dir: Optional[Path] = None):
        """Initialize FAI configuration generator.
        
        Args:
            base_config_dir: Directory containing base FAI configuration
            templates_dir: Directory containing Jinja2 templates
        """
        if base_config_dir is None:
            # Default to fai_config_base relative to project root
            project_root = Path(__file__).parent.parent.parent
            base_config_dir = project_root / "fai_config_base"
        
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"
        
        self.base_config_dir = Path(base_config_dir)
        self.templates_dir = Path(templates_dir)
        
        if not self.base_config_dir.exists():
            raise FAIConfigGenerationError(f"Base FAI config directory not found: {self.base_config_dir}")
        
        if not self.templates_dir.exists():
            raise FAIConfigGenerationError(f"Templates directory not found: {self.templates_dir}")
        
        # Configure Jinja2 environment for FAI class template
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    def generate_fai_config(self, 
                           config: BuildConfig,
                           output_dir: Path,
                           temp_dir: Optional[Path] = None) -> Path:
        """Generate complete FAI configuration space.
        
        Args:
            config: Build configuration object
            output_dir: Directory to create FAI configuration in
            temp_dir: Temporary directory for intermediate files
            
        Returns:
            Path to generated FAI configuration directory
            
        Raises:
            FAIConfigGenerationError: If generation fails
        """
        try:
            # Create output directory
            fai_config_dir = Path(output_dir) / "fai-config"
            if fai_config_dir.exists():
                shutil.rmtree(fai_config_dir)
            fai_config_dir.mkdir(parents=True)
            
            # Copy base configuration
            self._copy_base_configuration(fai_config_dir)
            
            # Generate dynamic class script
            self._generate_dynamic_class(config, fai_config_dir)
            
            # Generate custom package configuration
            self._generate_custom_packages(config, fai_config_dir)
            
            # Generate environment configuration
            self._generate_environment_config(config, fai_config_dir)
            
            # Apply configuration overlays
            self._apply_configuration_overlays(config, fai_config_dir)
            
            # Validate generated configuration
            self._validate_fai_configuration(fai_config_dir)
            
            logger.info(f"Generated FAI configuration: {fai_config_dir}")
            return fai_config_dir
            
        except Exception as e:
            raise FAIConfigGenerationError(f"Failed to generate FAI configuration: {e}")
    
    def _copy_base_configuration(self, fai_config_dir: Path) -> None:
        """Copy base FAI configuration to output directory.
        
        Args:
            fai_config_dir: Target FAI configuration directory
        """
        logger.info("Copying base FAI configuration...")
        
        # Copy all base configuration directories
        for item in self.base_config_dir.iterdir():
            target = fai_config_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        
        logger.debug(f"Copied base configuration from {self.base_config_dir}")
    
    def _generate_dynamic_class(self, config: BuildConfig, fai_config_dir: Path) -> None:
        """Generate dynamic FAI class script based on configuration.
        
        Args:
            config: Build configuration object
            fai_config_dir: FAI configuration directory
        """
        logger.info("Generating dynamic FAI class script...")
        
        try:
            template = self.env.get_template('fai-class.j2')
            
            # Prepare template context
            context = {
                'config': config,
                'build_timestamp': datetime.now().isoformat(),
                'fai_classes': config.get_fai_classes()
            }
            
            # Render dynamic class script
            content = template.render(**context)
            
            # Write to class directory with proper naming
            class_file = fai_config_dir / "class" / "40-DYNAMIC.sh"
            with open(class_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make executable
            class_file.chmod(0o755)
            
            logger.debug(f"Generated dynamic class script: {class_file}")
            
        except TemplateError as e:
            raise FAIConfigGenerationError(f"Template rendering error for dynamic class: {e}")
    
    def _generate_custom_packages(self, config: BuildConfig, fai_config_dir: Path) -> None:
        """Generate custom package configuration based on user settings.
        
        Args:
            config: Build configuration object
            fai_config_dir: FAI configuration directory
        """
        logger.info("Generating custom package configuration...")
        
        package_config_file = fai_config_dir / "package_config" / "CUSTOM_SOFTWARE"
        
        # Start with template header
        lines = [
            "# FAI package configuration for custom software",
            "# Dynamically generated from user configuration",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
            "PACKAGES install"
        ]
        
        # Add user-specified APT packages
        if config.packages.apt_packages:
            lines.extend([
                "",
                "# User-specified APT packages",
                *config.packages.apt_packages
            ])
        
        # Add hardware-specific packages placeholder
        lines.extend([
            "",
            "# Hardware-specific packages (populated by class scripts)",
            "# $HARDWARE_PACKAGES will be expanded during FAI execution"
        ])
        
        # Add encryption packages if needed
        if config.encryption.enabled:
            lines.extend([
                "",
                "# Encryption support packages",
                "cryptsetup",
                "cryptsetup-initramfs", 
                "lvm2"
            ])
        
        # Add development tools if detected
        dev_packages = ['git', 'vim', 'code', 'build-essential', 'python3-pip', 'nodejs', 'npm']
        user_dev_packages = [pkg for pkg in config.packages.apt_packages if pkg in dev_packages]
        
        if user_dev_packages:
            lines.extend([
                "",
                "# Development tools",
                "build-essential",
                "git",
                "vim"
            ])
        
        # Write package configuration
        with open(package_config_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        
        logger.debug(f"Generated package configuration: {package_config_file}")
    
    def _generate_environment_config(self, config: BuildConfig, fai_config_dir: Path) -> None:
        """Generate environment configuration for FAI variables.
        
        Args:
            config: Build configuration object
            fai_config_dir: FAI configuration directory
        """
        logger.info("Generating FAI environment configuration...")
        
        # Create environment configuration script
        env_script = fai_config_dir / "class" / "50-ENVIRONMENT.sh"
        
        env_vars = {
            # User configuration
            'FAI_USER_NAME': config.user.username,
            'FAI_USER_FULL_NAME': config.user.full_name,
            'FAI_SUDO_NOPASSWD': str(config.user.sudo_nopasswd).lower(),
            
            # Hardware configuration
            'FAI_HARDWARE_VENDOR': config.hardware.vendor.value,
            'FAI_TARGET_SSD': str(config.hardware.target_ssd).lower(),
            
            # Encryption configuration
            'FAI_ENCRYPTION_ENABLED': str(config.encryption.enabled).lower(),
            
            # Network configuration
            'FAI_HOSTNAME': config.network.hostname,
            'FAI_DHCP': str(config.network.dhcp).lower(),
            
            # First boot configuration
            'FAI_FIRST_BOOT_ENABLED': str(config.first_boot.enabled).lower(),
            
            # Build metadata
            'FAI_BUILD_TIMESTAMP': datetime.now().isoformat(),
            'FAI_ISO_LABEL': config.iso_label
        }
        
        # Add encryption-specific variables
        if config.encryption.enabled:
            env_vars.update({
                'LUKS_CIPHER': config.encryption.cipher,
                'LUKS_KEY_SIZE': str(config.encryption.key_size),
                'LUKS_HASH': 'sha256'  # Default secure hash
            })
        
        # Add package lists as comma-separated strings
        if config.packages.apt_packages:
            env_vars['CUSTOM_APT_PACKAGES'] = ' '.join(config.packages.apt_packages)
        
        if config.packages.deb_urls:
            env_vars['CUSTOM_DEB_URLS'] = ','.join(config.packages.deb_urls)
        
        if config.packages.snap_packages:
            env_vars['CUSTOM_SNAP_PACKAGES'] = ','.join(config.packages.snap_packages)
        
        # Add SSH keys if configured
        if config.user.ssh_authorized_keys:
            # Join multiple keys with newlines, escape for shell
            ssh_keys = '\\n'.join(config.user.ssh_authorized_keys)
            env_vars['FAI_SSH_KEYS'] = ssh_keys
        
        # Generate script content
        script_lines = [
            "#!/bin/bash",
            "# FAI environment configuration",
            "# Dynamically generated from user configuration",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
            "# Export configuration variables for use in FAI scripts",
        ]
        
        for var_name, var_value in env_vars.items():
            # Escape value for shell safety
            escaped_value = str(var_value).replace('"', '\\"').replace('$', '\\$')
            script_lines.append(f'export {var_name}="{escaped_value}"')
        
        script_lines.extend([
            "",
            "# Log environment setup",
            'echo "$(date): FAI environment configured" >> $LOGDIR/environment.log'
        ])
        
        # Write environment script
        with open(env_script, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines) + '\n')
        
        # Make executable
        env_script.chmod(0o755)
        
        logger.debug(f"Generated environment configuration: {env_script}")
    
    def _apply_configuration_overlays(self, config: BuildConfig, fai_config_dir: Path) -> None:
        """Apply configuration-specific overlays and modifications.
        
        Args:
            config: Build configuration object
            fai_config_dir: FAI configuration directory
        """
        logger.info("Applying configuration overlays...")
        
        # Select appropriate disk configuration
        if config.encryption.enabled:
            # Use encrypted disk configuration
            source_disk_config = "UBUNTU_ENCRYPTED"
        else:
            # Use standard disk configuration
            source_disk_config = "UBUNTU_DESKTOP"
        
        # The disk configurations are already in place, but we need to ensure
        # the correct one is used based on the classes assigned
        
        # Create a configuration selection script
        config_selector = fai_config_dir / "class" / "60-CONFIG_SELECTOR.sh"
        
        selector_content = f"""#!/bin/bash
# Configuration selector based on encryption settings
# Generated automatically

if [ "${{FAI_ENCRYPTION_ENABLED:-false}}" = "true" ]; then
    echo "UBUNTU_ENCRYPTED"
    echo "Using encrypted disk configuration"
else
    echo "UBUNTU_DESKTOP"  
    echo "Using standard disk configuration"
fi

# Log configuration selection
echo "$(date): Configuration selector applied" >> $LOGDIR/config-selector.log
"""
        
        with open(config_selector, 'w', encoding='utf-8') as f:
            f.write(selector_content)
        
        config_selector.chmod(0o755)
        
        logger.debug("Applied configuration overlays")
    
    def _validate_fai_configuration(self, fai_config_dir: Path) -> None:
        """Validate generated FAI configuration for completeness.
        
        Args:
            fai_config_dir: FAI configuration directory
            
        Raises:
            FAIConfigGenerationError: If validation fails
        """
        logger.info("Validating FAI configuration...")
        
        required_dirs = ['class', 'disk_config', 'package_config', 'scripts', 'hooks']
        missing_dirs = []
        
        for required_dir in required_dirs:
            dir_path = fai_config_dir / required_dir
            if not dir_path.exists():
                missing_dirs.append(required_dir)
        
        if missing_dirs:
            raise FAIConfigGenerationError(f"Missing required FAI directories: {missing_dirs}")
        
        # Check for essential files
        class_dir = fai_config_dir / "class"
        class_files = list(class_dir.glob("*.sh"))
        
        if not class_files:
            raise FAIConfigGenerationError("No class scripts found in configuration")
        
        # Validate disk configurations exist
        disk_config_dir = fai_config_dir / "disk_config"
        disk_configs = list(disk_config_dir.iterdir())
        
        if not disk_configs:
            raise FAIConfigGenerationError("No disk configurations found")
        
        logger.info("FAI configuration validation passed")


def generate_fai_configuration(config: BuildConfig, 
                              output_dir: Path,
                              base_config_dir: Optional[Path] = None) -> Path:
    """Convenience function to generate FAI configuration.
    
    Args:
        config: Build configuration object
        output_dir: Directory to create FAI configuration in
        base_config_dir: Base FAI configuration directory
        
    Returns:
        Path to generated FAI configuration directory
        
    Raises:
        FAIConfigGenerationError: If generation fails
    """
    generator = FAIConfigGenerator(base_config_dir=base_config_dir)
    return generator.generate_fai_config(config, output_dir)