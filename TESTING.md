# 🧪 Ubuntu FAI Build System - 测试指南

本文档提供了 Ubuntu FAI 构建系统的完整测试指南，包括单元测试、集成测试、配置验证和性能测试。

## 📋 目录

- [测试环境设置](#测试环境设置)
- [测试分类](#测试分类)
- [运行测试](#运行测试)
- [配置验证测试](#配置验证测试)
- [本地资源测试](#本地资源测试-新功能)
- [集成测试](#集成测试)
- [性能测试](#性能测试)
- [代码覆盖率](#代码覆盖率)
- [故障排除](#故障排除)
- [CI/CD 集成](#cicd-集成)

## 🛠️ 测试环境设置

### 1. 激活虚拟环境
```bash
# 如果还没有创建虚拟环境
./setup-venv.sh

# 激活虚拟环境
source ubuntu-fai-venv/bin/activate
```

### 2. 安装测试依赖
```bash
# 依赖已包含在 requirements.txt 中
pip install -r requirements.txt

# 验证测试工具安装
pytest --version
coverage --version
```

### 3. 验证环境
```bash
# 运行基础配置验证
python -c "
from src.config.models import BuildConfig
print('✅ 配置模型导入成功')
"

# 验证 JSON 配置格式
python -m json.tool config.json.example > /dev/null && echo "✅ JSON 格式正确"
```

## 📚 测试分类

### 🏗️ 测试目录结构
```
tests/
├── __init__.py
├── conftest.py                 # Pytest 配置和 fixtures
├── config/                     # 配置相关测试
│   ├── test_models.py         # 配置模型测试
│   └── test_validator.py      # 配置验证器测试
├── downloaders/               # 下载器测试
│   └── test_packages.py      # 包下载器测试
├── generators/                # 生成器测试
│   └── test_autoinstall.py   # Autoinstall 生成器测试
└── integration/               # 集成测试
    └── test_build_integration.py  # 构建集成测试
```

### 📊 测试类型

#### 1. **单元测试** (Unit Tests)
- **配置模型验证**: Pydantic 模型的字段验证和约束
- **生成器测试**: Jinja2 模板渲染和输出验证
- **工具函数测试**: 辅助函数和工具类测试

#### 2. **集成测试** (Integration Tests)
- **端到端构建流程**: 完整的配置生成流程
- **文件系统交互**: 文件读写和目录操作
- **外部工具集成**: FAI 命令调用测试

#### 3. **配置验证测试** (Configuration Tests)
- **JSON 格式验证**: 配置文件语法和结构
- **业务逻辑验证**: 跨字段约束和兼容性检查
- **🆕 本地资源验证**: 本地文件路径和权限检查

## 🚀 运行测试

### 基本测试命令

#### 运行所有测试
```bash
# 标准测试运行
pytest

# 详细输出
pytest -v

# 显示测试进度
pytest -v --tb=short
```

#### 运行特定测试类别
```bash
# 配置相关测试
pytest tests/config/

# 生成器测试
pytest tests/generators/

# 集成测试
pytest tests/integration/

# 🆕 本地资源功能测试
pytest tests/config/test_models.py::TestPackageConfig::test_local_paths -v
```

#### 运行特定测试
```bash
# 运行单个测试文件
pytest tests/config/test_models.py

# 运行特定测试类
pytest tests/config/test_models.py::TestBuildConfig

# 运行特定测试方法
pytest tests/config/test_models.py::TestBuildConfig::test_valid_config
```

### 并行测试执行
```bash
# 使用多进程加速测试 (需要安装 pytest-xdist)
pip install pytest-xdist
pytest -n auto

# 指定进程数
pytest -n 4
```

## ⚙️ 配置验证测试

### 1. 基础配置验证
```bash
# 测试示例配置文件
pytest tests/config/test_models.py::test_example_configs -v

# 验证所有配置示例
python -c "
import json
from src.config.models import BuildConfig

# 测试在线模式配置
with open('config.json.example') as f:
    config = BuildConfig.model_validate_json(f.read())
    print('✅ 在线模式配置验证通过')

# 🆕 测试本地模式配置 (如果文件存在)
try:
    with open('config-local.json.example') as f:
        config = BuildConfig.model_validate_json(f.read())
        print('✅ 本地模式配置验证通过')
except FileNotFoundError:
    print('⚠️  config-local.json.example 不存在，跳过本地模式测试')
"
```

### 2. 字段验证测试
```bash
# 测试必需字段验证
pytest tests/config/test_models.py::TestBuildConfig::test_required_fields -v

# 测试字段约束
pytest tests/config/test_models.py::TestEncryptionConfig::test_passphrase_validation -v

# 🆕 测试本地路径验证
pytest tests/config/test_models.py::TestPackageConfig::test_deb_local_paths_validation -v
```

### 3. 跨字段验证测试
```bash
# 测试硬件与加密兼容性
pytest tests/config/test_models.py::TestBuildConfig::test_dell_encryption_compatibility -v

# 测试用户认证配置
pytest tests/config/test_models.py::TestBuildConfig::test_user_auth_validation -v
```

## 🏠 本地资源测试 (新功能)

### 1. 准备测试环境
```bash
# 创建测试用本地资源
mkdir -p test_assets/{packages,scripts}

# 创建测试 .deb 文件 (空文件用于测试)
touch test_assets/packages/test-package.deb
touch test_assets/packages/another-package.deb

# 创建测试脚本
cat > test_assets/scripts/test-script.sh << 'EOF'
#!/bin/bash
echo "Test script executed"
EOF
chmod +x test_assets/scripts/test-script.sh
```

### 2. 本地资源配置测试
```bash
# 创建本地模式测试配置
cat > config-test-local.json << 'EOF'
{
  "hardware": {"vendor": "generic"},
  "encryption": {
    "enabled": false,
    "passphrase": "TestPassword123!"
  },
  "packages": {
    "deb_local_paths": [
      "./test_assets/packages/test-package.deb",
      "./test_assets/packages/another-package.deb"
    ],
    "deb_target_dir": "/opt/test-packages"
  },
  "user": {
    "username": "testuser",
    "password": "TestPass123!"
  },
  "first_boot": {
    "enabled": true,
    "scripts": [
      {
        "local_path": "./test_assets/scripts/test-script.sh",
        "type": "automated"
      }
    ],
    "scripts_target_dir": "/opt/test-scripts"
  },
  "network": {"hostname": "test-host"}
}
EOF

# 验证本地配置
python -c "
from src.config.models import BuildConfig
with open('config-test-local.json') as f:
    config = BuildConfig.model_validate_json(f.read())
    print('✅ 本地测试配置验证通过')
    print(f'🔍 本地 DEB 包数量: {len(config.packages.deb_local_paths)}')
    print(f'🔍 DEB 包目标目录: {config.packages.deb_target_dir}')
    print(f'🔍 脚本目标目录: {config.first_boot.scripts_target_dir}')
"
```

### 3. 本地资源构建测试
```bash
# 测试本地资源构建流程
./run.sh --use-local-assets --skip-fai --debug config-test-local.json

# 验证缓存目录中的文件
echo "📁 检查缓存目录:"
ls -la cache/packages/ 2>/dev/null || echo "缓存目录不存在"
ls -la cache/scripts/ 2>/dev/null || echo "缓存目录不存在"

# 清理测试文件
rm -f config-test-local.json
rm -rf test_assets/
```

### 4. 本地资源单元测试
```bash
# 运行本地资源相关的单元测试
pytest -k "local" -v

# 测试文件路径验证
pytest tests/config/test_models.py::TestFirstBootScript::test_local_path_validation -v

# 测试本地和远程资源互斥验证
pytest tests/config/test_models.py::TestFirstBootScript::test_url_local_path_mutual_exclusive -v
```

## 🔗 集成测试

### 1. 端到端构建测试
```bash
# 完整构建流程测试 (跳过 FAI)
pytest tests/integration/test_build_integration.py::test_full_build_process -v

# 🆕 本地资源集成测试
pytest tests/integration/test_build_integration.py::test_local_assets_build -v
```

### 2. 配置生成测试
```bash
# Autoinstall 配置生成
pytest tests/generators/test_autoinstall.py::test_generate_user_data -v

# FAI 配置生成
pytest tests/generators/test_fai_config.py::test_generate_fai_config -v
```

### 3. 文件系统集成测试
```bash
# 输出目录结构验证
python -c "
import os
from pathlib import Path

# 运行构建后检查输出
expected_files = [
    'output/user-data.yaml',
    'output/fai-config',
    'output/first-boot'
]

for file_path in expected_files:
    if Path(file_path).exists():
        print(f'✅ {file_path} 存在')
    else:
        print(f'❌ {file_path} 缺失')
"
```

## ⚡ 性能测试

### 1. 构建时间基准测试
```bash
# 测量配置生成时间
time ./run.sh --skip-downloads --skip-fai --debug config.json.example

# 🆕 比较本地资源 vs 下载模式性能
echo "=== 本地资源模式 ==="
time ./run.sh --use-local-assets --skip-fai config-local.json.example 2>/dev/null

echo "=== 跳过下载模式 ==="  
time ./run.sh --skip-downloads --skip-fai config.json.example 2>/dev/null
```

### 2. 内存使用测试
```bash
# 监控内存使用
/usr/bin/time -v python build.py --skip-fai config.json.example 2>&1 | grep -E "(Maximum resident set size|User time|System time)"
```

### 3. 大型配置测试
```bash
# 创建包含大量包的测试配置
python -c "
import json
from pathlib import Path

# 生成大型配置
large_config = {
    'hardware': {'vendor': 'generic'},
    'encryption': {'enabled': False, 'passphrase': 'Test123!'},
    'packages': {
        'apt_packages': [f'package-{i:03d}' for i in range(100)],
        'deb_urls': [],
        'snap_packages': [f'snap-{i:03d}' for i in range(50)]
    },
    'user': {'username': 'testuser', 'password': 'Test123!'},
    'first_boot': {'enabled': False, 'scripts': []},
    'network': {'hostname': 'large-test'}
}

with open('config-large-test.json', 'w') as f:
    json.dump(large_config, f, indent=2)

print('✅ 大型测试配置已生成: config-large-test.json')
"

# 测试大型配置处理
time python -c "
from src.config.models import BuildConfig
with open('config-large-test.json') as f:
    config = BuildConfig.model_validate_json(f.read())
    print(f'✅ 验证了包含 {len(config.packages.apt_packages)} 个 APT 包的配置')
"

# 清理
rm -f config-large-test.json
```

## 📊 代码覆盖率

### 1. 生成覆盖率报告
```bash
# 运行测试并生成覆盖率
pytest --cov=src --cov-report=html --cov-report=term-missing

# 仅查看覆盖率报告
coverage report

# 生成详细的 HTML 报告
coverage html
echo "📊 覆盖率报告: htmlcov/index.html"
```

### 2. 覆盖率目标
```bash
# 检查覆盖率是否达到目标 (85%)
pytest --cov=src --cov-fail-under=85
```

### 3. 特定模块覆盖率
```bash
# 检查配置模块覆盖率
pytest --cov=src.config --cov-report=term-missing tests/config/

# 🆕 检查新功能覆盖率
pytest --cov=src.config.models --cov-report=term-missing tests/config/test_models.py -k "local"
```

## 🔧 故障排除

### 常见测试问题

#### 1. 导入错误
```bash
# 确认 PYTHONPATH 设置
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python -c "from src.config.models import BuildConfig; print('✅ 导入成功')"
```

#### 2. 文件权限问题
```bash
# 检查测试文件权限
find tests/ -name "*.py" -not -perm 644 -exec chmod 644 {} \;
find test_assets/ -name "*.sh" -not -perm 755 -exec chmod 755 {} \; 2>/dev/null || true
```

#### 3. 🆕 本地文件不存在
```bash
# 创建测试所需的本地资源
mkdir -p local_assets/{packages,scripts}
touch local_assets/packages/dummy.deb
echo "#!/bin/bash\necho test" > local_assets/scripts/dummy.sh
chmod +x local_assets/scripts/dummy.sh
```

#### 4. JSON 配置错误
```bash
# 验证 JSON 格式
python -m json.tool config.json.example >/dev/null && echo "✅ JSON 格式正确"

# 🆕 验证本地配置
python -m json.tool config-local.json.example >/dev/null && echo "✅ 本地配置 JSON 格式正确"
```

#### 5. 虚拟环境问题
```bash
# 重新创建虚拟环境
deactivate 2>/dev/null || true
rm -rf ubuntu-fai-venv
./setup-venv.sh
source ubuntu-fai-venv/bin/activate
pip install -r requirements.txt
```

### 调试测试
```bash
# 运行单个测试并显示详细输出
pytest tests/config/test_models.py::TestBuildConfig::test_valid_config -v -s

# 使用 pdb 调试器
pytest --pdb tests/config/test_models.py::TestBuildConfig::test_valid_config

# 在失败时启动调试器
pytest --pdb-trace tests/config/
```

## 🚀 CI/CD 集成

### GitHub Actions 示例
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    # 🆕 本地资源功能测试
    - name: Test local assets functionality
      run: |
        mkdir -p test_assets/{packages,scripts}
        touch test_assets/packages/test.deb
        echo "#!/bin/bash" > test_assets/scripts/test.sh
        chmod +x test_assets/scripts/test.sh
        pytest -k "local" -v
```

### 本地 pre-commit 检查
```bash
# 安装 pre-commit
pip install pre-commit

# 创建 .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
EOF

# 安装 hooks
pre-commit install

# 运行检查
pre-commit run --all-files
```

## 📈 测试最佳实践

### 1. 测试编写指南
- **命名规范**: 测试函数使用 `test_` 前缀，清晰描述测试内容
- **单一职责**: 每个测试只验证一个功能点
- **🆕 本地资源测试**: 为新的本地文件功能编写专门测试
- **边界测试**: 测试边界条件和异常情况

### 2. 测试数据管理
```bash
# 使用 fixtures 管理测试数据
# tests/conftest.py 示例
import pytest
from pathlib import Path

@pytest.fixture
def temp_local_assets(tmp_path):
    """创建临时本地资源目录"""
    assets_dir = tmp_path / "local_assets"
    packages_dir = assets_dir / "packages"
    scripts_dir = assets_dir / "scripts"
    
    packages_dir.mkdir(parents=True)
    scripts_dir.mkdir(parents=True)
    
    # 创建测试文件
    (packages_dir / "test.deb").touch()
    script_file = scripts_dir / "test.sh"
    script_file.write_text("#!/bin/bash\necho 'test'")
    script_file.chmod(0o755)
    
    return assets_dir
```

### 3. 持续集成优化
- **并行执行**: 使用 `pytest-xdist` 加速测试
- **缓存依赖**: 缓存 pip 安装和虚拟环境
- **🆕 分层测试**: 本地资源测试与常规测试分离
- **失败快速反馈**: 优先运行快速的单元测试

## 🎯 测试检查清单

### 开发前检查
- [ ] 虚拟环境已激活
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 基础配置验证通过

### 🆕 本地资源功能检查
- [ ] 本地文件路径验证测试通过
- [ ] 本地与远程资源互斥验证
- [ ] 本地资源复制流程测试
- [ ] 目标目录配置测试

### 提交前检查
- [ ] 所有测试通过 (`pytest`)
- [ ] 代码覆盖率 ≥ 85% (`pytest --cov=src --cov-fail-under=85`)
- [ ] 配置文件验证通过
- [ ] 集成测试通过
- [ ] 本地资源功能测试通过

### 发布前检查
- [ ] 全面回归测试通过
- [ ] 性能基准测试正常
- [ ] 文档测试示例可运行
- [ ] CI/CD 流水线通过

---

📝 **注意**: 本测试指南涵盖了最新的本地资源管理功能。运行测试前请确保已按照 [README.md](README.md) 设置好环境。