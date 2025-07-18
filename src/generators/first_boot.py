"""First-boot configuration generator for Ubuntu FAI builds."""

import logging
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, Template

from ..config.models import BuildConfig, FirstBootConfig


class FirstBootGenerator:
    """Generates first-boot scripts and systemd services."""
    
    def __init__(self, templates_dir: Path = None):
        """Initialize first-boot generator.
        
        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def _prepare_context(self, config: BuildConfig) -> Dict[str, Any]:
        """Prepare template context from configuration.
        
        Args:
            config: Build configuration
            
        Returns:
            Template context dictionary
        """
        return {
            'config': config,
            'hardware': config.hardware,
            'encryption': config.encryption,
            'packages': config.packages,
            'user': config.user,
            'first_boot': config.first_boot,
            'network': config.network
        }
    
    def generate_first_boot_service(self, config: BuildConfig, output_path: Path) -> str:
        """Generate systemd service file for first-boot.
        
        Args:
            config: Build configuration
            output_path: Output file path
            
        Returns:
            Generated service file content
        """
        template = self.env.get_template('first-boot.service.j2')
        context = self._prepare_context(config)
        
        content = template.render(**context)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(content)
            self.logger.info(f"Generated first-boot service: {output_path}")
        
        return content
    
    def generate_first_boot_script(self, config: BuildConfig, output_path: Path) -> str:
        """Generate main first-boot script.
        
        Args:
            config: Build configuration
            output_path: Output file path
            
        Returns:
            Generated script content
        """
        template = self.env.get_template('first-boot-script.sh.j2')
        context = self._prepare_context(config)
        
        content = template.render(**context)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(content)
            # Make script executable
            output_path.chmod(0o755)
            self.logger.info(f"Generated first-boot script: {output_path}")
        
        return content
    
    def generate_config(self, config: BuildConfig, output_dir: Path) -> None:
        """Generate complete first-boot configuration.
        
        Args:
            config: Build configuration
            output_dir: Output directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Generating first-boot configuration in {output_dir}")
        
        # Generate systemd service
        service_path = output_dir / "first-boot.service"
        self.generate_first_boot_service(config, service_path)
        
        # Generate main script
        script_path = output_dir / "first-boot.sh"
        self.generate_first_boot_script(config, script_path)
        
        # Generate individual script files
        scripts_dir = output_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        for i, script_config in enumerate(config.first_boot.scripts):
            # Generate script name from URL or use index
            if script_config.url:
                url_path = urlparse(script_config.url).path
                filename = Path(url_path).name or f"script_{i}.sh"
                script_name = filename.replace('.sh', '')
            else:
                script_name = f"script_{i}"

            script_file = scripts_dir / f"{script_name}.sh"
            
            # If script has content, write it directly
            if hasattr(script_config, 'content') and script_config.content:
                with open(script_file, 'w') as f:
                    f.write(script_config.content)
                script_file.chmod(0o755)
                self.logger.info(f"Generated script: {script_file}")
        
        self.logger.info("First-boot configuration generation completed")