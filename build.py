#!/usr/bin/env python3
"""Ubuntu FAI Build System - Main Orchestration Script.

This script orchestrates the entire Ubuntu 24.04 Desktop ISO build process
using FAI (Fully Automatic Installation) with custom configurations.
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from src.config.models import BuildConfig
from src.config.validator import ConfigValidator
from src.generators.autoinstall import AutoinstallGenerator
from src.generators.fai_config import FAIConfigGenerator
from src.generators.first_boot import FirstBootGenerator
from src.downloaders import PackageDownloader, ScriptDownloader
from src.utils.logger import setup_logging, BuildLogger
from src.utils.asset_scanner import AssetScanner


class FAIBuilder:
    """Main FAI build orchestrator."""
    
    def __init__(self, config_path: Path, output_dir: Path, cache_dir: Path, 
                 build_logger: BuildLogger = None):
        """Initialize FAI builder.
        
        Args:
            config_path: Path to configuration file
            output_dir: Output directory for generated files
            cache_dir: Cache directory for downloads
            build_logger: Build logger instance
        """
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.build_logger = build_logger
        self.logger = build_logger.get_logger("builder") if build_logger else None
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.config: Optional[BuildConfig] = None
        self.validator = ConfigValidator()
        self.autoinstall_gen = AutoinstallGenerator()
        self.fai_config_gen = FAIConfigGenerator()
        self.first_boot_gen = FirstBootGenerator()
        
        # Timing information
        self.phase_timings = {}
    
    def load_and_validate_config(self) -> BuildConfig:
        """Load and validate configuration.
        
        Returns:
            Validated configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("config_validation")
        
        if self.logger:
            self.logger.info(f"Loading configuration from {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                import json
                config_data = json.load(f)
            
            # Validate with Pydantic
            config = BuildConfig(**config_data)
            
            # Additional validation
            validation_result = self.validator.validate_config(config)
            
            # Log validation results
            if self.build_logger:
                self.build_logger.log_config_validation(
                    str(self.config_path),
                    validation_result.is_valid,
                    validation_result.errors,
                    validation_result.warnings
                )
            
            if not validation_result.is_valid:
                raise ValueError(f"Configuration validation failed: {validation_result.errors}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    if self.logger:
                        self.logger.warning(f"Configuration warning: {warning}")
            
            self.config = config
            phase_duration = time.time() - phase_start
            self.phase_timings['config_validation'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("config_validation", True, phase_duration)
            if self.logger:
                self.logger.info("Configuration loaded and validated successfully")
            
            return config
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("config_validation", False, phase_duration)
            if self.logger:
                self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def download_assets(self) -> None:
        """Download required packages and scripts."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("asset_download")
        
        if self.logger:
            self.logger.info("Downloading required assets...")
        
        try:
            # Download packages
            with PackageDownloader(self.cache_dir / "packages") as pkg_downloader:
                packages = pkg_downloader.create_package_info_from_config(self.config.packages)
                if packages:
                    if self.logger:
                        self.logger.info(f"Downloading {len(packages)} packages...")
                    pkg_downloader.download_packages(packages)
            
            # Download scripts
            with ScriptDownloader(self.cache_dir / "scripts") as script_downloader:
                scripts = script_downloader.create_script_info_from_config(self.config.first_boot)
                if scripts:
                    if self.logger:
                        self.logger.info(f"Downloading {len(scripts)} scripts...")
                    script_downloader.download_scripts(scripts)
            
            phase_duration = time.time() - phase_start
            self.phase_timings['asset_download'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("asset_download", True, phase_duration)
            if self.logger:
                self.logger.info("Asset downloads completed")
                
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("asset_download", False, phase_duration)
            if self.logger:
                self.logger.error(f"Asset download failed: {e}")
            raise
    
    def scan_and_prepare_local_assets(self, base_dir: Path = None) -> None:
        """Automatically scan and prepare local assets from ./local_assets/ directory."""
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("asset_scanning")
        
        if self.logger:
            self.logger.info("Scanning for local assets...")
        
        try:
            import shutil
            
            # Initialize asset scanner
            scanner = AssetScanner(base_dir)
            
            # Scan all assets
            assets = scanner.scan_all()
            packages = assets['packages']
            scripts = assets['scripts']
            
            if self.logger:
                self.logger.info(f"Found {len(packages)} .deb packages and {len(scripts)} scripts")
            
            # Prepare packages
            if packages:
                packages_dir = self.cache_dir / "packages"
                packages_dir.mkdir(parents=True, exist_ok=True)
                
                for package in packages:
                    src_path = Path(package.path)
                    dst_path = packages_dir / package.name
                    shutil.copy2(src_path, dst_path)
                    if self.logger:
                        self.logger.info(f"Copied {package.name} (MD5: {package.md5[:8]}...)")
            
            # Prepare scripts
            if scripts:
                scripts_dir = self.cache_dir / "scripts"
                scripts_dir.mkdir(parents=True, exist_ok=True)
                
                for script in scripts:
                    src_path = Path(script.path)
                    dst_path = scripts_dir / script.name
                    shutil.copy2(src_path, dst_path)
                    # Make script executable
                    dst_path.chmod(0o755)
                    if self.logger:
                        self.logger.info(f"Copied {script.name} (SHA256: {script.sha256[:8]}...)")
            
            # Update configuration with discovered ISO file
            if assets['iso_files']:
                base_iso = assets['iso_files'][0]  # Use first ISO found
                # Update config with base ISO path
                self.config.base_iso_path = str(base_iso.path)
                self.config.base_iso_checksum = base_iso.sha256
                if self.logger:
                    self.logger.info(f"Found base ISO: {base_iso.name} (SHA256: {base_iso.sha256[:16]}...)")
            
            # Save asset manifest for verification
            manifest_path = scanner.save_asset_manifest()
            if self.logger:
                self.logger.info(f"Asset manifest saved: {manifest_path}")
            
            phase_duration = time.time() - phase_start
            self.phase_timings['asset_scanning'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("asset_scanning", True, phase_duration)
            if self.logger:
                self.logger.info("Asset scanning and preparation completed")
                
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("asset_scanning", False, phase_duration)
            if self.logger:
                self.logger.error(f"Asset scanning failed: {e}")
            raise

    def prepare_local_assets(self) -> None:
        """Prepare local packages and scripts by copying to cache directories."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("asset_preparation")
        
        if self.logger:
            self.logger.info("Preparing local assets...")
        
        try:
            import shutil
            
            # Prepare local .deb packages
            if self.config.packages.deb_local_paths:
                packages_dir = self.cache_dir / "packages"
                packages_dir.mkdir(parents=True, exist_ok=True)
                
                if self.logger:
                    self.logger.info(f"Copying {len(self.config.packages.deb_local_paths)} local .deb packages...")
                
                for local_path in self.config.packages.deb_local_paths:
                    src_path = Path(local_path)
                    dst_path = packages_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
                    if self.logger:
                        self.logger.info(f"Copied {src_path.name} to cache")
            
            # Prepare local scripts
            local_scripts = [s for s in self.config.first_boot.scripts if s.local_path]
            if local_scripts:
                scripts_dir = self.cache_dir / "scripts"
                scripts_dir.mkdir(parents=True, exist_ok=True)
                
                if self.logger:
                    self.logger.info(f"Copying {len(local_scripts)} local scripts...")
                
                for script in local_scripts:
                    src_path = Path(script.local_path)
                    dst_path = scripts_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
                    # Make script executable
                    dst_path.chmod(0o755)
                    if self.logger:
                        self.logger.info(f"Copied {src_path.name} to cache")
            
            phase_duration = time.time() - phase_start
            self.phase_timings['asset_preparation'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("asset_preparation", True, phase_duration)
            if self.logger:
                self.logger.info("Local asset preparation completed")
                
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("asset_preparation", False, phase_duration)
            if self.logger:
                self.logger.error(f"Local asset preparation failed: {e}")
            raise
    
    def generate_autoinstall_config(self) -> Path:
        """Generate Ubuntu autoinstall configuration.
        
        Returns:
            Path to generated user-data.yaml
        """
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("autoinstall_generation")
        
        if self.logger:
            self.logger.info("Generating autoinstall configuration...")
        
        try:
            output_path = self.output_dir / "user-data.yaml"
            self.autoinstall_gen.generate_user_data(self.config, output_path)
            
            phase_duration = time.time() - phase_start
            self.phase_timings['autoinstall_generation'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_template_generation(
                    "user-data.yaml.j2", str(output_path), True
                )
                self.build_logger.log_phase_end("autoinstall_generation", True, phase_duration)
            if self.logger:
                self.logger.info(f"Autoinstall configuration generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_template_generation(
                    "user-data.yaml.j2", str(self.output_dir / "user-data.yaml"), False
                )
                self.build_logger.log_phase_end("autoinstall_generation", False, phase_duration)
            if self.logger:
                self.logger.error(f"Autoinstall configuration generation failed: {e}")
            raise
    
    def generate_fai_config(self) -> Path:
        """Generate FAI configuration files.
        
        Returns:
            Path to generated FAI config directory
        """
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("fai_generation")
        
        if self.logger:
            self.logger.info("Generating FAI configuration...")
        
        try:
            fai_config_dir = self.output_dir / "fai-config"
            self.fai_config_gen.generate_fai_config(self.config, fai_config_dir)
            
            phase_duration = time.time() - phase_start
            self.phase_timings['fai_generation'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("fai_generation", True, phase_duration)
            if self.logger:
                self.logger.info(f"FAI configuration generated: {fai_config_dir}")
            
            return fai_config_dir
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("fai_generation", False, phase_duration)
            if self.logger:
                self.logger.error(f"FAI configuration generation failed: {e}")
            raise
    
    def generate_first_boot_config(self) -> Path:
        """Generate first-boot configuration.
        
        Returns:
            Path to generated first-boot directory
        """
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("first_boot_generation")
        
        if self.logger:
            self.logger.info("Generating first-boot configuration...")
        
        try:
            first_boot_dir = self.output_dir / "first-boot"
            self.first_boot_gen.generate_config(self.config, first_boot_dir)
            
            phase_duration = time.time() - phase_start
            self.phase_timings['first_boot_generation'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("first_boot_generation", True, phase_duration)
            if self.logger:
                self.logger.info(f"First-boot configuration generated: {first_boot_dir}")
            
            return first_boot_dir
            
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("first_boot_generation", False, phase_duration)
            if self.logger:
                self.logger.error(f"First-boot configuration generation failed: {e}")
            raise
    
    def run_fai_build(self, fai_config_dir: Path) -> Path:
        """Execute FAI build process.
        
        Args:
            fai_config_dir: Path to FAI configuration directory
            
        Returns:
            Path to generated ISO file
        """
        import subprocess
        
        phase_start = time.time()
        if self.build_logger:
            self.build_logger.log_phase_start("fai_build")
        
        if self.logger:
            self.logger.info("Starting FAI build process...")
        
        iso_output = self.output_dir / f"ubuntu-{self.config.hardware.vendor.lower()}-custom.iso"
        
        # FAI build command
        fai_cmd = [
            "fai-cd",
            "-f",  # Force overwrite
            "-g",  # Use GRUB
            "-B", str(fai_config_dir),  # Base configuration directory
        ]
        
        # Add base ISO or mirror URL
        if self.config.base_iso_path:
            # Use local ISO file with mirror directory
            fai_cmd.extend(["-S", str(self.config.base_iso_path)])
            fai_cmd.extend(["-m", "http://archive.ubuntu.com/ubuntu"])
            if self.logger:
                self.logger.info(f"Using local base ISO: {self.config.base_iso_path}")
                self.logger.info("Using mirror for package updates: http://archive.ubuntu.com/ubuntu")
        else:
            # Use mirror URL for online build
            fai_cmd.extend(["-M", "http://archive.ubuntu.com/ubuntu"])
            if self.logger:
                self.logger.info("Using online mirror for base system")
        
        fai_cmd.append(str(iso_output))
        
        try:
            if self.logger:
                self.logger.info(f"Running FAI command: {' '.join(fai_cmd)}")
            
            result = subprocess.run(
                fai_cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                phase_duration = time.time() - phase_start
                if self.build_logger:
                    self.build_logger.log_phase_end("fai_build", False, phase_duration)
                if self.logger:
                    self.logger.error(f"FAI build failed: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, fai_cmd, result.stderr)
            
            phase_duration = time.time() - phase_start
            self.phase_timings['fai_build'] = phase_duration
            
            if self.build_logger:
                self.build_logger.log_phase_end("fai_build", True, phase_duration)
            if self.logger:
                self.logger.info("FAI build completed successfully")
                self.logger.info(f"ISO file generated: {iso_output}")
            
            return iso_output
            
        except subprocess.TimeoutExpired:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("fai_build", False, phase_duration)
            if self.logger:
                self.logger.error("FAI build timed out after 1 hour")
            raise
        except Exception as e:
            phase_duration = time.time() - phase_start
            if self.build_logger:
                self.build_logger.log_phase_end("fai_build", False, phase_duration)
            if self.logger:
                self.logger.error(f"FAI build failed: {e}")
            raise
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        if self.logger:
            self.logger.info("Cleaning up temporary files...")
        # Additional cleanup logic can be added here
    
    def build(self, skip_downloads: bool = False, skip_fai: bool = False, use_local_assets: bool = False, scan_assets: bool = False) -> Path:
        """Execute complete build process.
        
        Args:
            skip_downloads: Skip asset downloads
            skip_fai: Skip FAI build (generate configs only)
            use_local_assets: Use local assets instead of downloading
            scan_assets: Automatically scan ./local_assets/ directory for assets
            
        Returns:
            Path to generated ISO file (if FAI build is executed)
        """
        build_start = time.time()
        
        try:
            # Load and validate configuration
            self.load_and_validate_config()
            
            # Handle assets
            if scan_assets:
                self.scan_and_prepare_local_assets()
            elif use_local_assets:
                self.prepare_local_assets()
            elif not skip_downloads:
                self.download_assets()
            else:
                if self.logger:
                    self.logger.info("Skipping asset downloads as requested")
            
            # Generate configurations
            autoinstall_path = self.generate_autoinstall_config()
            fai_config_dir = self.generate_fai_config()
            first_boot_dir = self.generate_first_boot_config()
            
            # Execute FAI build
            if not skip_fai:
                iso_path = self.run_fai_build(fai_config_dir)
                
                # Log successful build with timing summary
                total_build_time = time.time() - build_start
                if self.logger:
                    self.logger.info(f"Complete build finished in {total_build_time:.2f}s")
                    if self.phase_timings:
                        self.logger.info("Phase timings:")
                        for phase, duration in self.phase_timings.items():
                            self.logger.info(f"  {phase}: {duration:.2f}s")
                
                return iso_path
            else:
                if self.logger:
                    self.logger.info("Skipping FAI build as requested")
                
                # Log configuration generation completion
                total_time = time.time() - build_start
                if self.logger:
                    self.logger.info(f"Configuration generation completed in {total_time:.2f}s")
                    if self.phase_timings:
                        self.logger.info("Phase timings:")
                        for phase, duration in self.phase_timings.items():
                            self.logger.info(f"  {phase}: {duration:.2f}s")
                
                return self.output_dir
                
        except Exception as e:
            if self.logger:
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
        "--use-local-assets",
        action="store_true",
        help="Use local assets instead of downloading (requires local file paths in config)"
    )
    
    parser.add_argument(
        "--scan-assets",
        action="store_true",
        help="Automatically scan ./local_assets/ directory for .deb files and scripts"
    )
    
    parser.add_argument(
        "--skip-fai",
        action="store_true",
        help="Skip FAI build process (generate configs only)"
    )
    
    args = parser.parse_args()
    
    # Setup enhanced logging
    build_logger = setup_logging(debug=args.debug)
    logger = build_logger.get_logger("main")
    
    # Validate arguments
    if not args.config.exists():
        logger.error(f"Configuration file not found: {args.config}")
        return 1
    
    # Start build session
    build_start_time = time.time()
    build_logger.log_build_start(str(args.config))
    
    try:
        # Initialize builder
        builder = FAIBuilder(
            config_path=args.config,
            output_dir=args.output_dir,
            cache_dir=args.cache_dir,
            build_logger=build_logger
        )
        
        # Execute build
        result_path = builder.build(
            skip_downloads=args.skip_downloads,
            skip_fai=args.skip_fai,
            use_local_assets=args.use_local_assets,
            scan_assets=args.scan_assets
        )
        
        # Calculate total build time
        total_duration = time.time() - build_start_time
        build_logger.log_build_end(True, total_duration)
        
        if args.skip_fai:
            logger.info(f"Configuration files generated in: {result_path}")
        else:
            logger.info(f"Build completed successfully: {result_path}")
        
        # Create session summary
        build_logger.create_session_summary()
        
        return 0
        
    except KeyboardInterrupt:
        total_duration = time.time() - build_start_time
        build_logger.log_build_end(False, total_duration)
        logger.warning("Build interrupted by user")
        return 130
    except Exception as e:
        total_duration = time.time() - build_start_time
        build_logger.log_build_end(False, total_duration)
        logger.error(f"Build failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())