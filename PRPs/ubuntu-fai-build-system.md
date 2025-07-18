name: "Ubuntu FAI Build System - Complete Implementation PRP v1.0"
description: |

## Purpose
Comprehensive PRP for implementing a Python-based build system that generates custom Ubuntu 24.04 Desktop ISOs using FAI (Fully Automatic Installation) as the core engine, running entirely in Docker with configuration-driven automation.

## Core Principles
1. **Context is King**: All documentation, FAI concepts, Ubuntu Autoinstall patterns included
2. **Validation Loops**: Executable tests and lints for iterative development  
3. **Information Dense**: Leverages researched patterns and best practices
4. **Progressive Success**: Modular implementation following CLAUDE.md guidelines
5. **Docker-First**: Reproducible build environment with pinned dependencies

---

## Goal
Build a complete Python orchestration system that generates bootable Ubuntu 24.04 Desktop ISOs with:
- LUKS full-disk encryption with LVM targeting SSDs
- Custom APT package installation 
- Dynamic .deb package and script downloads from URLs
- First-boot automation (both interactive and non-interactive scripts)
- Hardware-specific FAI classes (Dell, Lenovo, HP)
- Configuration validation using Pydantic v2
- Jinja2 template-driven configuration generation

## Why
- **Reproducible Infrastructure**: Eliminate manual installation inconsistencies
- **Security First**: Built-in LUKS encryption for enterprise deployments
- **Developer Productivity**: Single config.json controls entire build process
- **Portability**: Docker-based builds work across macOS, Linux, Windows
- **Automation Ready**: Integrates with CI/CD pipelines for large-scale deployments

## What
User provides a config.json file specifying:
- Target hardware vendor (Dell/Lenovo/HP)
- Custom software packages (APT + direct .deb URLs)
- LUKS encryption settings and disk targeting
- First-boot script URLs and execution preferences
- User accounts and SSH keys

System generates a bootable ISO that automatically installs Ubuntu 24.04 with all specified customizations.

### Success Criteria
- [ ] Docker container builds without errors
- [ ] config.json validation catches malformed configurations
- [ ] Generates valid user-data.yaml for Ubuntu Autoinstall
- [ ] Creates proper FAI configuration space structure
- [ ] Downloads and integrates custom packages/scripts
- [ ] Produces bootable ISO via FAI commands
- [ ] LUKS encryption works on target SSDs
- [ ] First-boot scripts execute as configured

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window

- url: https://fai-project.org/fai-guide/
  why: Core FAI concepts - classes, hooks, configuration space structure
  critical: FAI uses uppercase class names, specific directory structure, and NFS-based config distribution

- url: https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html
  why: Ubuntu Autoinstall user-data.yaml syntax, LUKS+LVM patterns
  critical: Must use top-level 'autoinstall:' key, validate against JSON schema

- url: https://docs.pydantic.dev/latest/concepts/validators/
  why: Pydantic v2 field validation, model configuration patterns
  critical: Use @field_validator instead of deprecated @validator, ValidationInfo.data for cross-field validation

- url: https://jinja.palletsprojects.com/en/stable/templates/
  why: Template inheritance, variable substitution, YAML generation best practices
  critical: Use trim_blocks=True and lstrip_blocks=True for clean YAML output

- file: /Users/bytedance/Documents/Workspace/Ubuntu-FAI/CLAUDE.md
  why: Project-specific patterns, 500-line limit, modular design requirements
  critical: Never create files >500 lines, use relative imports, follow testing patterns

- doc: https://testdriven.io/blog/docker-best-practices/
  why: Docker multi-stage builds, reproducible patterns for Python
  critical: Pin base images with specific tags, use python:3.12-slim-bullseye for reproducibility
```

### Current Codebase Tree
```bash
Ubuntu-FAI/
├── CLAUDE.md                    # Project instructions and patterns
├── INITIAL.md                   # Feature requirements specification  
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md         # PRP template structure
│   └── ubuntu-fai-build-system.md  # This PRP
└── README.md                    # Minimal project readme
```

### Desired Codebase Tree with Files to be Added
```bash
Ubuntu-FAI/
├── build.py                          # Main orchestrator script (<500 lines)
├── run.sh                           # Docker entry point for macOS/Linux
├── Dockerfile                       # Ubuntu 24.04 + Python 3.12 + FAI
├── requirements.txt                 # Pinned dependencies with hashes
├── config.json.example             # Complete configuration template
├── README.md                        # Comprehensive setup documentation
├── 
├── src/                            # Core Python modules
│   ├── __init__.py
│   ├── config/                     # Configuration handling (<500 lines total)
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic v2 models for config.json
│   │   └── validator.py           # Custom validation logic
│   ├── templates/                  # Jinja2 templates for dynamic generation
│   │   ├── user-data.yaml.j2      # Ubuntu Autoinstall configuration
│   │   ├── first-boot.service.j2  # Systemd service for first-boot
│   │   └── fai-class.j2           # Dynamic FAI class generation
│   ├── generators/                 # Template rendering modules (<500 lines each)
│   │   ├── __init__.py
│   │   ├── autoinstall.py         # Generate user-data.yaml from config
│   │   ├── fai_config.py          # Generate FAI configuration space
│   │   └── first_boot.py          # Generate first-boot script packages
│   ├── downloaders/                # Asset acquisition modules (<500 lines each)
│   │   ├── __init__.py
│   │   ├── packages.py            # Download .deb files from URLs
│   │   └── scripts.py             # Download scripts and validate checksums
│   └── utils/                      # Shared utilities (<500 lines each)
│       ├── __init__.py
│       ├── filesystem.py          # Path handling, temp directories
│       └── docker_utils.py        # Docker environment detection
├── 
├── fai_config_base/               # FAI configuration space (static base)
│   ├── class/                     # FAI class definitions (shell scripts)
│   │   ├── 10-UBUNTU_DESKTOP.sh  # Base Ubuntu Desktop setup
│   │   ├── 20-HARDWARE.sh        # Dell/Lenovo/HP hardware detection
│   │   └── 30-ENCRYPTION.sh      # LUKS+LVM encryption logic
│   ├── disk_config/               # Partitioning configurations
│   │   ├── UBUNTU_DESKTOP        # Standard ext4 partitioning
│   │   └── UBUNTU_ENCRYPTED      # LUKS+LVM partitioning scheme
│   ├── package_config/            # Package installation lists
│   │   ├── UBUNTU_DESKTOP        # Base desktop packages
│   │   └── CUSTOM_SOFTWARE       # Dynamic package list generation
│   ├── scripts/                   # FAI customization scripts
│   │   ├── UBUNTU_DESKTOP/        # Desktop environment configuration
│   │   └── CUSTOM_SOFTWARE/       # Custom package installation logic
│   └── hooks/                     # FAI lifecycle hooks
│       ├── partition.PRE_PARTITION  # Pre-partitioning setup
│       └── instsoft.POST_INSTSOFT  # Post-software installation
├── 
├── first_boot_scripts/            # Scripts executed on first boot
│   ├── automated/                 # Non-interactive automation
│   │   ├── 01-system-setup.sh    # System-level configuration
│   │   └── 02-user-config.sh     # User environment setup
│   └── manual/                    # Interactive configuration
│       └── 01-user-interaction.sh # Manual setup prompts
├── 
└── tests/                         # Comprehensive test suite
    ├── __init__.py
    ├── test_config/               # Configuration validation tests
    │   ├── test_models.py         # Pydantic model validation tests
    │   └── test_validator.py      # Custom validation logic tests
    ├── test_generators/           # Template generation tests
    │   ├── test_autoinstall.py    # Autoinstall YAML generation tests
    │   └── test_fai_config.py     # FAI configuration generation tests
    ├── fixtures/                  # Test data and expected outputs
    │   ├── config_valid.json      # Valid configuration examples
    │   ├── config_invalid.json    # Invalid configuration test cases
    │   └── expected_outputs/       # Expected template generation results
    └── integration/               # End-to-end integration tests
        └── test_build_process.py   # Full build process validation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FAI requires specific directory structure and naming conventions
# FAI classes must be UPPERCASE, scripts use numeric prefixes for execution order
# FAI configuration space must be accessible via NFS in production

# CRITICAL: Ubuntu Autoinstall syntax requirements
# Must use top-level 'autoinstall:' key in user-data.yaml
# LUKS passwords must be provided as plain text (security consideration)
# Storage configuration 'match' patterns for SSD detection: {"ssd": true, "size": "largest"}

# CRITICAL: Pydantic v2 breaking changes
# @validator is deprecated, use @field_validator instead
# ValidationInfo.data replaces 'values' parameter for cross-field validation
# Use ConfigDict instead of Config class for model configuration

# CRITICAL: Jinja2 YAML templating gotchas  
# Use trim_blocks=True and lstrip_blocks=True to prevent extra whitespace
# YAML is indentation-sensitive, use proper spacing in templates
# Use safe filters for any user-provided content to prevent injection

# CRITICAL: Docker build optimization for reproducibility
# Pin base image to specific Ubuntu 24.04 SHA256 for reproducible builds  
# Use multi-stage builds to reduce final image size
# Install FAI tools in container: fai-server, fai-client, fai-cd packages

# CRITICAL: FAI + Docker integration challenges
# FAI expects to run as root with full system access
# Container needs privileged mode for ISO creation
# Loop device access required for mounting generated ISOs
```

## Implementation Blueprint

### Data Models and Structure
Core configuration validation using Pydantic v2 with robust error handling:
```python
# src/config/models.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Union
from pathlib import Path

class HardwareConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    vendor: str = Field(..., pattern="^(dell|lenovo|hp)$")
    target_ssd: bool = Field(default=True)
    
class EncryptionConfig(BaseModel):
    enabled: bool = Field(default=True)
    passphrase: str = Field(..., min_length=12)
    
class PackageConfig(BaseModel):
    apt_packages: List[str] = Field(default_factory=list)
    deb_urls: List[str] = Field(default_factory=list)
    
    @field_validator('deb_urls')
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        # Validate URL format and .deb extension
        return v

class BuildConfig(BaseModel):
    """Main configuration model for Ubuntu FAI build system"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    hardware: HardwareConfig
    encryption: EncryptionConfig
    packages: PackageConfig
    first_boot_scripts: List[str] = Field(default_factory=list)
```

### List of Tasks to be Completed (Implementation Order)

```yaml
Task 1: Setup Build Environment
CREATE Dockerfile:
  - BASE: ubuntu:24.04 (pinned with SHA256)
  - INSTALL: python3.12, python3-pip, fai-server, fai-client, fai-cd
  - USER: Create non-root user for most operations
  - WORKDIR: /app for application code

CREATE requirements.txt:
  - PIN: pydantic==2.5.*, jinja2==3.1.*, pyyaml==6.0.*, requests==2.31.*
  - INCLUDE: pytest, black, mypy for development tools
  - GENERATE: pip-compile for dependency locking

CREATE run.sh:
  - DOCKER BUILD: Build container with tagged name
  - DOCKER RUN: Execute build.py with volume mounts
  - PERMISSION: Handle macOS/Linux file permission mapping

Task 2: Configuration Management System  
CREATE src/config/models.py:
  - IMPLEMENT: Pydantic v2 models for complete config.json schema
  - VALIDATE: Hardware vendor selection, encryption settings
  - PATTERN: Use @field_validator for URL and package validation

CREATE src/config/validator.py:
  - IMPLEMENT: Cross-field validation logic (encryption + hardware)
  - VALIDATE: Package dependencies and compatibility
  - ERROR: Detailed validation error messages with suggestions

CREATE config.json.example:
  - PROVIDE: Complete example with all options documented
  - INCLUDE: Comments explaining each configuration section
  - EXAMPLES: Different hardware configurations (Dell/Lenovo/HP)

Task 3: Template System Implementation
CREATE src/templates/user-data.yaml.j2:
  - IMPLEMENT: Ubuntu Autoinstall configuration template
  - SUPPORT: LUKS+LVM encryption with dynamic disk targeting
  - PATTERN: Follow canonical autoinstall schema exactly

CREATE src/templates/first-boot.service.j2:
  - IMPLEMENT: Systemd service for first-boot script execution
  - HANDLE: Both automated and interactive script execution
  - SECURITY: Proper service isolation and error handling

CREATE src/generators/autoinstall.py:
  - IMPLEMENT: Jinja2 template rendering for user-data.yaml
  - VALIDATE: Generated YAML against autoinstall schema
  - ERROR: Meaningful error messages for template failures

Task 4: FAI Configuration Generation
CREATE fai_config_base/class/10-UBUNTU_DESKTOP.sh:
  - IMPLEMENT: Base Ubuntu Desktop class definition
  - SET: Required FAI variables for desktop installation
  - PATTERN: Follow FAI class naming and variable conventions

CREATE src/generators/fai_config.py:
  - IMPLEMENT: Dynamic FAI configuration space generation
  - COPY: Base FAI config and overlay dynamic customizations
  - INTEGRATE: Custom package lists and hardware-specific settings

CREATE fai_config_base/disk_config/UBUNTU_ENCRYPTED:
  - IMPLEMENT: LUKS+LVM partitioning scheme for FAI
  - TARGET: SSD detection and automatic disk selection
  - SECURE: Proper LUKS key management and LVM setup

Task 5: Asset Download System
CREATE src/downloaders/packages.py:
  - IMPLEMENT: Download .deb packages from URLs with validation
  - VERIFY: Package signatures and checksums when available
  - CACHE: Downloaded packages to avoid repeated downloads

CREATE src/downloaders/scripts.py:
  - IMPLEMENT: Download first-boot scripts from URLs
  - VALIDATE: Script syntax and security scanning
  - ORGANIZE: Scripts by execution type (automated/manual)

Task 6: Main Orchestration Logic
CREATE build.py:
  - IMPLEMENT: Main build orchestration logic (<500 lines)
  - SEQUENCE: Config validation → Template generation → Asset download → FAI execution
  - ERROR: Comprehensive error handling with cleanup
  - LOGGING: Detailed progress logging for debugging

Task 7: First-Boot Script System
CREATE first_boot_scripts/automated/01-system-setup.sh:
  - IMPLEMENT: Base system configuration automation
  - CONFIGURE: Network, users, security settings
  - PATTERN: Idempotent operations with proper error handling

CREATE src/generators/first_boot.py:
  - IMPLEMENT: First-boot script generation and packaging
  - INTEGRATE: Downloaded scripts with base automation
  - SCHEDULE: Proper execution order and dependency handling

Task 8: Comprehensive Testing
CREATE tests/test_config/test_models.py:
  - TEST: Pydantic model validation (happy path + edge cases)
  - VALIDATE: Error handling for malformed configurations
  - COVER: All configuration combinations and hardware types

CREATE tests/test_generators/test_autoinstall.py:
  - TEST: Ubuntu Autoinstall YAML generation accuracy
  - VALIDATE: Generated configuration against official schema
  - VERIFY: LUKS+LVM configuration correctness

CREATE tests/integration/test_build_process.py:
  - TEST: End-to-end build process with sample configurations
  - VALIDATE: Generated ISO structure and bootability
  - VERIFY: All components integrate correctly

Task 9: Documentation and Examples
UPDATE README.md:
  - DOCUMENT: Complete setup instructions for macOS/Linux
  - EXPLAIN: Project structure and component responsibilities
  - PROVIDE: Troubleshooting guide and common issues

Task 10: Production Validation
IMPLEMENT validation gates:
  - SYNTAX: Black formatting, mypy type checking
  - UNIT: All pytest tests passing with >90% coverage
  - INTEGRATION: Sample ISO generation and validation
  - SECURITY: Static analysis for configuration injection
```

### Per Task Pseudocode

```python
# Task 1: Dockerfile - Reproducible FAI build environment
FROM ubuntu:24.04@sha256:specific_hash  # Pin for reproducibility
RUN apt-get update && apt-get install -y \
    python3.12 python3-pip \
    fai-server fai-client fai-cd \
    && rm -rf /var/lib/apt/lists/*  # Clean cache for smaller image
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# PATTERN: Multi-stage build for production optimization

# Task 2: Pydantic v2 configuration validation
class BuildConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('hardware_vendor')
    @classmethod
    def validate_vendor(cls, v: str, info: ValidationInfo) -> str:
        # PATTERN: Cross-field validation using ValidationInfo.data
        encryption = info.data.get('encryption', {})
        if v == 'dell' and encryption.get('enabled'):
            # GOTCHA: Dell-specific LUKS compatibility check
            pass
        return v

# Task 3: Jinja2 template rendering with YAML safety
env = Environment(
    loader=FileSystemLoader('src/templates'),
    trim_blocks=True,          # CRITICAL: Clean YAML output
    lstrip_blocks=True,        # CRITICAL: Prevent indentation issues  
    autoescape=False           # GOTCHA: YAML doesn't need HTML escaping
)
template = env.get_template('user-data.yaml.j2')
# PATTERN: Validate generated YAML with PyYAML.safe_load()

# Task 6: Main orchestration with comprehensive error handling
async def main_build_process(config_path: Path) -> None:
    try:
        # PATTERN: Fail fast with detailed error context
        config = validate_config(config_path)  
        assets = await download_assets(config)  # Parallel downloads
        templates = generate_templates(config, assets)
        iso_path = await execute_fai_build(templates)
        logger.info(f"ISO generated successfully: {iso_path}")
    except ValidationError as e:
        # PATTERN: User-friendly error messages with suggestions
        logger.error(f"Configuration error: {e.errors()}")
        sys.exit(1)
```

### Integration Points
```yaml
DOCKER:
  - volume: Mount config.json and output directory
  - network: Container needs internet for package downloads
  - privileges: Requires --privileged for loop device access

FAI:
  - config_space: Generate in /tmp/fai-config for build
  - nfs: Not required for single-build scenarios
  - output: ISO generated in configurable output directory

UBUNTU_AUTOINSTALL:
  - validation: Verify against canonical JSON schema
  - testing: Use qemu for bootability testing
  - security: LUKS passphrase handling and cleanup

FIRST_BOOT:
  - systemd: Install service during FAI installation
  - execution: Scripts run on first successful boot
  - cleanup: Remove service after completion
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
black src/ tests/ build.py --check        # Code formatting
mypy src/ build.py --strict               # Type checking
ruff check src/ tests/ build.py --fix     # Linting with auto-fix

# Expected: No errors. If errors exist, READ them carefully and fix.
```

### Level 2: Unit Tests
```bash
# Create comprehensive test coverage for each new module
pytest tests/test_config/ -v              # Configuration validation tests
pytest tests/test_generators/ -v          # Template generation tests
pytest tests/test_downloaders/ -v         # Asset download tests

# Each test file should include:
# - test_happy_path(): Basic functionality works
# - test_validation_error(): Invalid input handling  
# - test_edge_cases(): Boundary conditions and empty inputs
```

### Level 3: Integration Test
```bash
# Test complete build process with sample configuration
python build.py config.json.example       # Full build test
ls -la output/                            # Verify ISO creation
file output/*.iso                         # Confirm ISO file type

# Expected: Successful ISO generation without errors
# If errors: Check build logs and FAI output for details
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v --cov=src --cov-report=term-missing`
- [ ] No linting errors: `ruff check src/ tests/ build.py`
- [ ] No type errors: `mypy src/ build.py --strict`
- [ ] Docker build successful: `docker build -t ubuntu-fai .`
- [ ] Sample ISO generation: `./run.sh config.json.example`
- [ ] Config validation works: Test with invalid configurations
- [ ] Documentation complete: README.md covers all setup steps
- [ ] Security review: No hardcoded credentials or injection risks

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode FAI paths - use configurable directories
- ❌ Don't skip Pydantic validation - always validate config.json
- ❌ Don't ignore Docker layer optimization - use multi-stage builds  
- ❌ Don't store passwords in logs - sanitize logging output
- ❌ Don't assume root execution - handle permission requirements properly
- ❌ Don't skip cleanup - remove temporary files and downloaded assets
- ❌ Don't ignore FAI error codes - properly handle build failures

## Confidence Score: 9/10
This PRP provides comprehensive context, detailed implementation steps, and executable validation gates. The systematic approach covers all major technical challenges: FAI integration, Ubuntu Autoinstall configuration, Pydantic v2 validation, Docker reproducibility, and Jinja2 templating. One-pass implementation should succeed with careful attention to the documented gotchas and validation loops.