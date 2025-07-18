#!/usr/bin/env python3
"""Ubuntu FAI Build System - Main Orchestration Script.

This script orchestrates the entire Ubuntu 24.04 Desktop ISO build process
using FAI (Fully Automatic Installation) with custom configurations.
"""

import argparse
import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

from src.config.models import BuildConfig
from src.config.validator import ConfigValidator
from src.generators.autoinstall import AutoinstallGenerator
from src.generators.fai_config import FAIConfigGenerator
from src.generators.first_boot import FirstBootGenerator
from src.downloaders import PackageDownloader, ScriptDownloader


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the build process.
    
    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('build.log')
        ]
    )


class FAIBuilder:
    """Main FAI build orchestrator."""
    
    def __init__(self, config_path: Path, output_dir: Path, cache_dir: Path):
        """Initialize FAI builder.
        
        Args:
            config_path: Path to configuration file
            output_dir: Output directory for generated files
            cache_dir: Cache directory for downloads
        """
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.config: Optional[BuildConfig] = None
        self.validator = ConfigValidator()
        self.autoinstall_gen = AutoinstallGenerator()
        self.fai_config_gen = FAIConfigGenerator()
        self.first_boot_gen = FirstBootGenerator()
    
    def load_and_validate_config(self) -> BuildConfig:
        """Load and validate configuration.
        
        Returns:
            Validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.logger.info(f"Loading configuration from {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                import json
                config_data = json.load(f)
            
            # Validate with Pydantic
            config = BuildConfig(**config_data)
            
            # Additional validation
            validation_result = self.validator.validate_config(config)
            if not validation_result.is_valid:
                raise ValueError(f"Configuration validation failed: {validation_result.errors}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    self.logger.warning(f"Configuration warning: {warning}")
            
            self.config = config
            self.logger.info("Configuration loaded and validated successfully")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def download_assets(self) -> None:
        """Download required packages and scripts."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        self.logger.info("Downloading required assets...")
        
        # Download packages
        with PackageDownloader(self.cache_dir / "packages") as pkg_downloader:
            packages = pkg_downloader.create_package_info_from_config(self.config.packages)
            if packages:
                self.logger.info(f"Downloading {len(packages)} packages...")
                pkg_downloader.download_packages(packages)
        
        # Download scripts
        with ScriptDownloader(self.cache_dir / "scripts") as script_downloader:
            scripts = script_downloader.create_script_info_from_config(self.config.first_boot)
            if scripts:
                self.logger.info(f"Downloading {len(scripts)} scripts...")
                script_downloader.download_scripts(scripts)
        
        self.logger.info("Asset downloads completed")
    
    def generate_autoinstall_config(self) -> Path:
        """Generate Ubuntu autoinstall configuration.
        
        Returns:
            Path to generated user-data.yaml
        """
        self.logger.info("Generating autoinstall configuration...")
        
        output_path = self.output_dir / "user-data.yaml"
        self.autoinstall_gen.generate_user_data(self.config, output_path)
        
        self.logger.info(f"Autoinstall configuration generated: {output_path}")
        return output_path
    
    def generate_fai_config(self) -> Path:
        """Generate FAI configuration files.
        
        Returns:
            Path to generated FAI config directory
        """
        self.logger.info("Generating FAI configuration...")
        
        fai_config_dir = self.output_dir / "fai-config"
        self.fai_config_gen.generate_config(self.config, fai_config_dir)
        
        self.logger.info(f"FAI configuration generated: {fai_config_dir}")
        return fai_config_dir
    
    def generate_first_boot_config(self) -> Path:
        """Generate first-boot configuration.
        
        Returns:
            Path to generated first-boot directory
        """
        self.logger.info("Generating first-boot configuration...")
        
        first_boot_dir = self.output_dir / "first-boot"
        self.first_boot_gen.generate_config(self.config, first_boot_dir)
        
        self.logger.info(f"First-boot configuration generated: {first_boot_dir}")
        return first_boot_dir
    
    def run_fai_build(self, fai_config_dir: Path) -> Path:
        """Execute FAI build process.
        
        Args:
            fai_config_dir: Path to FAI configuration directory
            
        Returns:
            Path to generated ISO file
        """
        import subprocess
        
        self.logger.info("Starting FAI build process...")
        
        iso_output = self.output_dir / f"ubuntu-{self.config.hardware.vendor.lower()}-custom.iso"
        
        # FAI build command
        fai_cmd = [
            "fai-cd",
            "-f",  # Force overwrite
            "-g",  # Use GRUB
            "-B", str(fai_config_dir),  # Base configuration directory
            "-M",  # Mirror
            str(iso_output)
        ]
        
        try:
            self.logger.info(f"Running FAI command: {' '.join(fai_cmd)}")
            
            result = subprocess.run(
                fai_cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"FAI build failed: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, fai_cmd, result.stderr)
            
            self.logger.info("FAI build completed successfully")
            self.logger.info(f"ISO file generated: {iso_output}")
            
            return iso_output
            
        except subprocess.TimeoutExpired:
            self.logger.error("FAI build timed out after 1 hour")
            raise
        except Exception as e:
            self.logger.error(f"FAI build failed: {e}")
            raise
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        self.logger.info("Cleaning up temporary files...")
        # Additional cleanup logic can be added here
    
    def build(self, skip_downloads: bool = False, skip_fai: bool = False) -> Path:
        """Execute complete build process.
        
        Args:
            skip_downloads: Skip asset downloads
            skip_fai: Skip FAI build (generate configs only)
            
        Returns:
            Path to generated ISO file (if FAI build is executed)
        """
        try:
            # Load and validate configuration
            self.load_and_validate_config()
            
            # Download assets
            if not skip_downloads:
                self.download_assets()
            
            # Generate configurations
            autoinstall_path = self.generate_autoinstall_config()
            fai_config_dir = self.generate_fai_config()
            first_boot_dir = self.generate_first_boot_config()
            
            # Execute FAI build
            if not skip_fai:
                iso_path = self.run_fai_build(fai_config_dir)
                return iso_path
            else:
                self.logger.info("Skipping FAI build as requested")
                return self.output_dir
                
        except Exception as e:
            self.logger.error(f"Build failed: {e}")
            raise
        finally:
            self.cleanup_temp_files()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ubuntu FAI Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s config.json                    # Full build
  %(prog)s --debug config.json            # Debug build
  %(prog)s --output-dir /tmp config.json  # Custom output
  %(prog)s --skip-fai config.json         # Generate configs only
  %(prog)s --skip-downloads config.json   # Use cached downloads
        """
    )
    
    parser.add_argument(
        "config",
        type=Path,
        help="Path to configuration JSON file"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="./output",
        help="Output directory for generated files (default: ./output)"
    )
    
    parser.add_argument(
        "--cache-dir", 
        type=Path,
        default="./cache",
        help="Cache directory for downloads (default: ./cache)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--skip-downloads",
        action="store_true", 
        help="Skip asset downloads (use cached files)"
    )
    
    parser.add_argument(
        "--skip-fai",
        action="store_true",
        help="Skip FAI build process (generate configs only)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    if not args.config.exists():
        logger.error(f"Configuration file not found: {args.config}")
        return 1
    
    try:
        # Initialize builder
        builder = FAIBuilder(
            config_path=args.config,
            output_dir=args.output_dir,
            cache_dir=args.cache_dir
        )
        
        # Execute build
        result_path = builder.build(
            skip_downloads=args.skip_downloads,
            skip_fai=args.skip_fai
        )
        
        if args.skip_fai:
            logger.info(f"Configuration files generated in: {result_path}")
        else:
            logger.info(f"Build completed successfully: {result_path}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Build interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Build failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())