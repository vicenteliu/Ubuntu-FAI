"""Asset scanner for automatic local resource discovery and verification."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class AssetInfo:
    """Information about a local asset file."""
    
    path: str
    name: str
    size: int
    md5: str
    sha256: str
    type: str  # 'deb' or 'script'
    executable: bool = False


class AssetScanner:
    """Scanner for discovering and analyzing local assets."""
    
    def __init__(self, base_dir: Path = None):
        """Initialize asset scanner.
        
        Args:
            base_dir: Base directory to scan (defaults to ./local_assets)
        """
        if base_dir is None:
            base_dir = Path.cwd() / "local_assets"
        
        self.base_dir = Path(base_dir)
        self.packages_dir = self.base_dir / "packages"
        self.scripts_dir = self.base_dir / "scripts"
        self.iso_dir = self.base_dir / "iso"
        
        if logger:
            logger.info(f"Asset scanner initialized for: {self.base_dir}")
    
    def _calculate_hashes(self, file_path: Path) -> Tuple[str, str]:
        """Calculate MD5 and SHA256 hashes for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (md5_hash, sha256_hash)
        """
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return md5_hash.hexdigest(), sha256_hash.hexdigest()
            
        except Exception as e:
            if logger:
                logger.error(f"Failed to calculate hashes for {file_path}: {e}")
            raise
    
    def _scan_directory(self, directory: Path, file_type: str, 
                       extensions: List[str] = None) -> List[AssetInfo]:
        """Scan a directory for assets.
        
        Args:
            directory: Directory to scan
            file_type: Type of files ('deb' or 'script')
            extensions: List of file extensions to include
            
        Returns:
            List of AssetInfo objects
        """
        assets = []
        
        if not directory.exists():
            if logger:
                logger.warning(f"Directory does not exist: {directory}")
            return assets
        
        if logger:
            logger.info(f"Scanning {directory} for {file_type} files...")
        
        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue
            
            # Check extension if specified
            if extensions and file_path.suffix not in extensions:
                continue
            
            try:
                # Calculate file size
                size = file_path.stat().st_size
                
                # Calculate hashes
                md5_hash, sha256_hash = self._calculate_hashes(file_path)
                
                # Check if executable
                is_executable = file_path.stat().st_mode & 0o111 != 0
                
                # Create relative path
                relative_path = file_path.relative_to(self.base_dir.parent)
                
                asset = AssetInfo(
                    path=str(relative_path),
                    name=file_path.name,
                    size=size,
                    md5=md5_hash,
                    sha256=sha256_hash,
                    type=file_type,
                    executable=is_executable
                )
                
                assets.append(asset)
                
                if logger:
                    logger.info(f"Found {file_type}: {file_path.name} "
                              f"(size: {size} bytes, MD5: {md5_hash[:8]}...)")
                    
            except Exception as e:
                if logger:
                    logger.error(f"Error processing {file_path}: {e}")
                continue
        
        return assets
    
    def scan_packages(self) -> List[AssetInfo]:
        """Scan for .deb package files.
        
        Returns:
            List of package AssetInfo objects
        """
        return self._scan_directory(
            self.packages_dir, 
            'deb', 
            extensions=['.deb']
        )
    
    def scan_scripts(self) -> List[AssetInfo]:
        """Scan for script files.
        
        Returns:
            List of script AssetInfo objects
        """
        return self._scan_directory(
            self.scripts_dir,
            'script',
            extensions=['.sh', '.py', '.pl', '.rb']  # Common script extensions
        )
    
    def scan_iso_files(self) -> List[AssetInfo]:
        """Scan for ISO files.
        
        Returns:
            List of ISO AssetInfo objects
        """
        return self._scan_directory(
            self.iso_dir,
            'iso',
            extensions=['.iso']
        )
    
    def scan_all(self) -> Dict[str, List[AssetInfo]]:
        """Scan all asset types.
        
        Returns:
            Dictionary with 'packages', 'scripts', and 'iso_files' keys
        """
        return {
            'packages': self.scan_packages(),
            'scripts': self.scan_scripts(),
            'iso_files': self.scan_iso_files()
        }
    
    def generate_config_snippet(self, include_checksums: bool = True) -> Dict:
        """Generate configuration snippet for discovered assets.
        
        Args:
            include_checksums: Whether to include checksums in output
            
        Returns:
            Configuration dictionary snippet
        """
        assets = self.scan_all()
        
        config = {
            "packages": {
                "deb_local_paths": [asset.path for asset in assets['packages']],
                "deb_target_dir": "/opt/packages"
            },
            "first_boot": {
                "enabled": bool(assets['scripts']),
                "scripts": [],
                "scripts_target_dir": "/opt/scripts"
            }
        }
        
        # Add base ISO if found
        iso_files = assets['iso_files']
        if iso_files:
            # Use the first ISO file found as base ISO
            base_iso = iso_files[0]
            config["base_iso_path"] = base_iso.path
            if include_checksums:
                config["base_iso_checksum"] = base_iso.sha256
        
        # Add scripts with checksums
        for script in assets['scripts']:
            script_config = {
                "local_path": script.path,
                "type": "automated"
            }
            
            if include_checksums:
                script_config["checksum"] = script.sha256
            
            config["first_boot"]["scripts"].append(script_config)
        
        return config
    
    def save_asset_manifest(self, output_path: Path = None) -> Path:
        """Save detailed asset manifest to JSON file.
        
        Args:
            output_path: Path to save manifest (defaults to local_assets/manifest.json)
            
        Returns:
            Path to saved manifest file
        """
        if output_path is None:
            output_path = self.base_dir / "manifest.json"
        
        assets = self.scan_all()
        
        # Convert AssetInfo objects to dictionaries
        manifest = {
            "scan_time": str(Path().cwd()),  # Current working directory as context
            "base_directory": str(self.base_dir),
            "summary": {
                "total_packages": len(assets['packages']),
                "total_scripts": len(assets['scripts']),
                "total_iso_files": len(assets['iso_files']),
                "total_size_bytes": sum(asset.size for asset_list in assets.values() 
                                      for asset in asset_list)
            },
            "packages": [
                {
                    "path": asset.path,
                    "name": asset.name,
                    "size": asset.size,
                    "md5": asset.md5,
                    "sha256": asset.sha256,
                    "type": asset.type
                }
                for asset in assets['packages']
            ],
            "scripts": [
                {
                    "path": asset.path,
                    "name": asset.name,
                    "size": asset.size,
                    "md5": asset.md5,
                    "sha256": asset.sha256,
                    "type": asset.type,
                    "executable": asset.executable
                }
                for asset in assets['scripts']
            ],
            "iso_files": [
                {
                    "path": asset.path,
                    "name": asset.name,
                    "size": asset.size,
                    "md5": asset.md5,
                    "sha256": asset.sha256,
                    "type": asset.type
                }
                for asset in assets['iso_files']
            ]
        }
        
        # Save manifest
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        if logger:
            logger.info(f"Asset manifest saved to: {output_path}")
        
        return output_path
    
    def verify_assets(self, manifest_path: Path = None) -> List[str]:
        """Verify assets against a previously saved manifest.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            List of verification error messages (empty if all OK)
        """
        if manifest_path is None:
            manifest_path = self.base_dir / "manifest.json"
        
        if not manifest_path.exists():
            return [f"Manifest file not found: {manifest_path}"]
        
        errors = []
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Get current assets
            current_assets = self.scan_all()
            
            # Verify packages
            manifest_packages = {pkg['path']: pkg for pkg in manifest['packages']}
            current_packages = {asset.path: asset for asset in current_assets['packages']}
            
            for path, manifest_pkg in manifest_packages.items():
                if path not in current_packages:
                    errors.append(f"Package missing: {path}")
                else:
                    current_pkg = current_packages[path]
                    if current_pkg.sha256 != manifest_pkg['sha256']:
                        errors.append(f"Package checksum mismatch: {path}")
            
            # Verify scripts
            manifest_scripts = {script['path']: script for script in manifest['scripts']}
            current_scripts = {asset.path: asset for asset in current_assets['scripts']}
            
            for path, manifest_script in manifest_scripts.items():
                if path not in current_scripts:
                    errors.append(f"Script missing: {path}")
                else:
                    current_script = current_scripts[path]
                    if current_script.sha256 != manifest_script['sha256']:
                        errors.append(f"Script checksum mismatch: {path}")
            
            # Verify ISO files
            if 'iso_files' in manifest:
                manifest_iso_files = {iso['path']: iso for iso in manifest['iso_files']}
                current_iso_files = {asset.path: asset for asset in current_assets['iso_files']}
                
                for path, manifest_iso in manifest_iso_files.items():
                    if path not in current_iso_files:
                        errors.append(f"ISO file missing: {path}")
                    else:
                        current_iso = current_iso_files[path]
                        if current_iso.sha256 != manifest_iso['sha256']:
                            errors.append(f"ISO file checksum mismatch: {path}")
            
        except Exception as e:
            errors.append(f"Error reading manifest: {e}")
        
        return errors
    
    def print_summary(self) -> None:
        """Print a summary of discovered assets to console."""
        assets = self.scan_all()
        
        print(f"\n📂 Local Assets Summary (Base: {self.base_dir})")
        print("=" * 60)
        
        # Packages summary
        packages = assets['packages']
        if packages:
            print(f"\n📦 DEB Packages ({len(packages)} found):")
            for pkg in packages:
                size_mb = pkg.size / (1024 * 1024)
                print(f"  • {pkg.name}")
                print(f"    Path: {pkg.path}")
                print(f"    Size: {size_mb:.2f} MB")
                print(f"    MD5:    {pkg.md5}")
                print(f"    SHA256: {pkg.sha256}")
                print()
        else:
            print(f"\n📦 DEB Packages: None found in {self.packages_dir}")
        
        # Scripts summary
        scripts = assets['scripts']
        if scripts:
            print(f"\n📜 Scripts ({len(scripts)} found):")
            for script in scripts:
                size_kb = script.size / 1024
                executable_status = "✓ Executable" if script.executable else "✗ Not executable"
                print(f"  • {script.name} ({executable_status})")
                print(f"    Path: {script.path}")
                print(f"    Size: {size_kb:.1f} KB")
                print(f"    MD5:    {script.md5}")
                print(f"    SHA256: {script.sha256}")
                print()
        else:
            print(f"\n📜 Scripts: None found in {self.scripts_dir}")
        
        # ISO files summary
        iso_files = assets['iso_files']
        if iso_files:
            print(f"\n💿 ISO Files ({len(iso_files)} found):")
            for iso_file in iso_files:
                size_gb = iso_file.size / (1024 * 1024 * 1024)
                print(f"  • {iso_file.name}")
                print(f"    Path: {iso_file.path}")
                print(f"    Size: {size_gb:.2f} GB")
                print(f"    MD5:    {iso_file.md5}")
                print(f"    SHA256: {iso_file.sha256}")
                print()
        else:
            print(f"\n💿 ISO Files: None found in {self.iso_dir}")
        
        # Total summary
        total_size = sum(asset.size for asset_list in assets.values() for asset in asset_list)
        total_files = len(packages) + len(scripts) + len(iso_files)
        
        print(f"\n📊 Total: {total_files} files, {total_size / (1024 * 1024):.2f} MB")
        print("=" * 60)


def main():
    """CLI entry point for asset scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scan local assets and generate checksums"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default="./local_assets",
        help="Base directory to scan (default: ./local_assets)"
    )
    parser.add_argument(
        "--save-manifest",
        action="store_true",
        help="Save asset manifest to JSON file"
    )
    parser.add_argument(
        "--verify-manifest",
        type=Path,
        help="Verify assets against manifest file"
    )
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate configuration snippet"
    )
    parser.add_argument(
        "--no-checksums",
        action="store_true",
        help="Exclude checksums from generated config"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    # Initialize scanner
    scanner = AssetScanner(args.base_dir)
    
    if args.verify_manifest:
        errors = scanner.verify_assets(args.verify_manifest)
        if errors:
            print("❌ Verification failed:")
            for error in errors:
                print(f"  • {error}")
            exit(1)
        else:
            print("✅ All assets verified successfully")
            exit(0)
    
    # Print summary
    scanner.print_summary()
    
    # Save manifest if requested
    if args.save_manifest:
        manifest_path = scanner.save_asset_manifest()
        print(f"\n💾 Manifest saved to: {manifest_path}")
    
    # Generate config if requested
    if args.generate_config:
        config = scanner.generate_config_snippet(
            include_checksums=not args.no_checksums
        )
        print(f"\n⚙️  Configuration snippet:")
        print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()