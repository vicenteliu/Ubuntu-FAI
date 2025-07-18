"""Tests for autoinstall generator."""

import tempfile
import yaml
from pathlib import Path
import pytest

from src.generators.autoinstall import AutoinstallGenerator


class TestAutoinstallGenerator:
    """Test autoinstall configuration generator."""
    
    def setup_method(self):
        """Set up test method."""
        self.generator = AutoinstallGenerator()
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator is not None
        assert hasattr(self.generator, 'env')
        assert hasattr(self.generator, 'logger')
    
    def test_prepare_template_context(self, sample_build_config):
        """Test template context preparation."""
        context = self.generator._prepare_template_context(sample_build_config)
        
        assert isinstance(context, dict)
        assert 'config' in context
        assert 'hardware' in context
        assert 'encryption' in context
        assert 'packages' in context
        assert 'user' in context
        assert 'first_boot' in context
        assert 'network' in context
        
        # Check specific values
        assert context['hardware'].vendor == "Dell"
        assert context['user'].username == "testuser"
        assert context['encryption'].enabled is True
    
    def test_generate_user_data_content(self, sample_build_config):
        """Test user-data YAML generation content."""
        content = self.generator.generate_user_data(sample_build_config)
        
        assert isinstance(content, str)
        assert len(content) > 0
        
        # Parse as YAML to ensure it's valid
        try:
            data = yaml.safe_load(content)
            assert isinstance(data, dict)
            
            # Check for expected autoinstall structure
            assert 'autoinstall' in data
            autoinstall = data['autoinstall']
            
            # Check required sections
            assert 'version' in autoinstall
            assert 'identity' in autoinstall
            assert 'packages' in autoinstall
            
            # Check identity section
            identity = autoinstall['identity']
            assert identity['username'] == sample_build_config.user.username
            assert identity['realname'] == sample_build_config.user.full_name
            
        except yaml.YAMLError as e:
            pytest.fail(f"Generated YAML is invalid: {e}")
    
    def test_generate_user_data_with_encryption(self, sample_build_config):
        """Test user-data generation with encryption enabled."""
        # Ensure encryption is enabled
        sample_build_config.encryption.enabled = True
        
        content = self.generator.generate_user_data(sample_build_config)
        data = yaml.safe_load(content)
        
        # Check for encryption configuration
        autoinstall = data['autoinstall']
        assert 'storage' in autoinstall
        
        # Storage layout should include encryption
        storage = autoinstall['storage']
        assert isinstance(storage, dict)
        
        # Look for encryption indicators in the config
        content_lower = content.lower()
        assert 'crypt' in content_lower or 'luks' in content_lower
    
    def test_generate_user_data_with_packages(self, sample_build_config):
        """Test user-data generation with custom packages."""
        content = self.generator.generate_user_data(sample_build_config)
        data = yaml.safe_load(content)
        
        autoinstall = data['autoinstall']
        assert 'packages' in autoinstall
        
        packages = autoinstall['packages']
        assert isinstance(packages, list)
        
        # Check if our sample packages are included
        package_names = [pkg for pkg in packages if isinstance(pkg, str)]
        assert 'git' in package_names
        assert 'curl' in package_names
    
    def test_generate_user_data_to_file(self, sample_build_config, temp_dir):
        """Test user-data generation to file."""
        output_path = temp_dir / "user-data.yaml"
        
        content = self.generator.generate_user_data(sample_build_config, output_path)
        
        # Check file was created
        assert output_path.exists()
        
        # Check file content matches returned content
        with open(output_path, 'r') as f:
            file_content = f.read()
        
        assert file_content == content
        
        # Verify it's valid YAML
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert isinstance(data, dict)
        assert 'autoinstall' in data
    
    def test_yaml_syntax_validation(self, sample_build_config):
        """Test YAML syntax validation."""
        content = self.generator.generate_user_data(sample_build_config)
        
        # Should not raise any exception
        try:
            self.generator._validate_yaml_syntax(content)
        except Exception as e:
            pytest.fail(f"Valid YAML failed validation: {e}")
    
    def test_invalid_yaml_syntax_validation(self):
        """Test YAML syntax validation with invalid content."""
        invalid_yaml = """
        autoinstall:
          version: 1
          identity:
            username: testuser
            - invalid: yaml: structure
        """
        
        with pytest.raises(Exception):
            self.generator._validate_yaml_syntax(invalid_yaml)
    
    def test_generate_user_data_without_encryption(self, sample_build_config):
        """Test user-data generation without encryption."""
        # Disable encryption
        sample_build_config.encryption.enabled = False
        
        content = self.generator.generate_user_data(sample_build_config)
        data = yaml.safe_load(content)
        
        autoinstall = data['autoinstall']
        
        # Storage should be simpler without encryption
        if 'storage' in autoinstall:
            storage = autoinstall['storage']
            content_lower = content.lower()
            # Should not contain encryption references
            assert 'luks' not in content_lower
    
    def test_hardware_specific_configuration(self, sample_build_config):
        """Test hardware-specific configuration generation."""
        # Test with different vendors
        vendors = ["Dell", "Lenovo", "HP"]
        
        for vendor in vendors:
            sample_build_config.hardware.vendor = vendor
            content = self.generator.generate_user_data(sample_build_config)
            
            # Should generate valid YAML regardless of vendor
            data = yaml.safe_load(content)
            assert isinstance(data, dict)
            assert 'autoinstall' in data
    
    def test_context_hardware_detection(self, sample_build_config):
        """Test hardware detection in template context."""
        context = self.generator._prepare_template_context(sample_build_config)
        
        # Test hardware detection logic
        vendor = context['hardware'].vendor.lower()
        
        assert vendor in ['dell', 'lenovo', 'hp'] or vendor == sample_build_config.hardware.vendor.lower()
        
        # Test vendor-specific flags
        is_dell = vendor == 'dell'
        is_lenovo = vendor == 'lenovo'
        is_hp = vendor == 'hp'
        
        assert isinstance(is_dell, bool)
        assert isinstance(is_lenovo, bool)
        assert isinstance(is_hp, bool)