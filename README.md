# Ubuntu FAI Build System

🚀 **自动化 Ubuntu 24.04 Desktop ISO 构建系统**

使用 FAI (Fully Automatic Installation) 和 Python 的现代化 Ubuntu 定制 ISO 构建工具，支持本地资源管理和在线下载两种模式。

## 🌟 特性

### 🔧 核心功能
- **🐍 Python 虚拟环境**: 使用 Python venv 管理依赖，确保环境隔离和可重现性
- **⚙️ 智能配置验证**: 基于 Pydantic v2 的强类型配置验证和错误检查
- **🎨 模板化生成**: 使用 Jinja2 模板生成 autoinstall 和 FAI 配置
- **📊 增强日志系统**: 多级别日志记录，支持控制台、文件和 JSON 格式输出
- **⏱️ 构建时间追踪**: 详细的阶段计时和性能分析

### 🔒 安全与硬件
- **🔒 加密支持**: 内置 LUKS 磁盘加密配置，支持多种加密算法
- **🖥️ 硬件适配**: 支持 Dell、Lenovo、HP 等主流硬件厂商的专用配置
- **🔑 SSH 密钥管理**: 支持 SSH 公钥认证和用户权限配置

### 📦 资源管理 (新功能)
- **🔍 自动资源扫描**: 🆕 自动扫描 `./local_assets/` 目录，获取文件名和哈希值
- **🏠 本地资源支持**: 支持使用本地 .deb 文件和脚本，无需下载
- **💿 本地 ISO 支持**: 🆕 支持使用本地 Ubuntu ISO 文件，实现完全离线构建
- **🌐 在线下载模式**: 支持从 URL 下载 .deb 包和脚本文件
- **📁 自定义目标路径**: 可指定文件在目标系统中的安装位置
- **🔐 文件完整性验证**: 自动计算 MD5 和 SHA256 校验和
- **📋 资源清单管理**: 生成和验证详细的资源清单文件

### 🛠️ 软件安装
- **📦 多包管理器**: 支持 APT、Snap、DEB 包的自动安装
- **🔧 首次启动脚本**: 自动化首次启动配置和软件安装
- **⚡ 并行处理**: 支持批量文件复制和处理

## 🛠️ 系统要求

### 必需依赖
- **Ubuntu 24.04 LTS** (推荐)
- **Python 3.9+**
- **python3-venv** (虚拟环境模块)

### 系统包安装
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip git

# 可选：FAI 工具 (用于实际 ISO 构建)
sudo apt install fai-server fai-setup-storage fai-client
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd Ubuntu-FAI
```

### 2. 设置 Python 虚拟环境
```bash
./setup-venv.sh
```

### 3. 验证安装
```bash
# 测试配置生成
./run.sh --skip-fai config.json.example

# 测试本地资源功能
./run.sh --use-local-assets --skip-fai config-local.json.example

# 🆕 测试自动资源扫描功能
./run.sh --scan-assets --skip-fai config.json.example
```

### 4. 创建自定义配置
```bash
cp config.json.example my-config.json
# 编辑 my-config.json 根据需要自定义配置
```

## 📋 使用方法

### 基本构建命令

#### 在线模式 (下载资源)
```bash
# 完整构建 (生成配置 + 构建 ISO)
./run.sh my-config.json

# 仅生成配置文件
./run.sh --skip-fai my-config.json

# 跳过下载 (使用缓存)
./run.sh --skip-downloads my-config.json
```

#### 本地模式 (使用本地资源) 🆕
```bash
# 使用本地 .deb 文件和脚本
./run.sh --use-local-assets --skip-fai config-local.json.example

# 🆕 自动扫描并使用本地资源
./run.sh --scan-assets --skip-fai config.json.example

# 本地模式完整构建
./run.sh --use-local-assets my-config.json
```

#### 调试和测试
```bash
# 调试模式
./run.sh --debug --skip-fai my-config.json

# 跳过所有外部依赖
./run.sh --skip-downloads --skip-fai my-config.json
```

### 命令行选项
- `--scan-assets`: 🆕 自动扫描 `./local_assets/` 目录中的文件
- `--use-local-assets`: 🆕 使用本地资源而非下载
- `--skip-downloads`: 跳过资源下载阶段
- `--skip-fai`: 跳过 FAI ISO 构建阶段
- `--debug`: 启用调试模式，显示详细日志
- `--help`: 显示帮助信息

## 📁 本地资源使用 (新功能)

### 🔍 自动资源扫描模式 🆕

#### 1. 准备本地资源目录
```bash
mkdir -p local_assets/{packages,scripts,iso}
```

#### 2. 放置文件
```bash
# 将 .deb 文件放入 packages 目录
cp /path/to/chrome.deb local_assets/packages/
cp /path/to/vscode.deb local_assets/packages/

# 将脚本文件放入 scripts 目录
cp /path/to/setup.sh local_assets/scripts/
cp /path/to/config.sh local_assets/scripts/

# 🆕 将 Ubuntu ISO 文件放入 iso 目录
cp /path/to/ubuntu-24.04.1-desktop-amd64.iso local_assets/iso/

# 确保脚本文件具有执行权限
chmod +x local_assets/scripts/*.sh
```

#### 3. 自动扫描并构建
```bash
# 自动扫描 local_assets 目录并生成配置
./run.sh --scan-assets --skip-fai config.json.example

# 完整构建流程（自动扫描 + 构建 ISO）
./run.sh --scan-assets my-config.json
```

#### 4. 查看扫描结果
```bash
# 使用资源扫描工具查看详细信息
python3 -m src.utils.asset_scanner --base-dir ./local_assets --generate-config

# 生成资源清单文件
python3 -m src.utils.asset_scanner --base-dir ./local_assets --save-manifest

# 验证资源完整性
python3 -m src.utils.asset_scanner --verify-manifest ./local_assets/manifest.json
```

### 📝 手动配置模式

#### 1. 准备本地资源目录
```bash
mkdir -p local_assets/{packages,scripts,iso}
```

#### 2. 放置文件
```bash
# 将 .deb 文件放入 packages 目录
cp /path/to/chrome.deb local_assets/packages/
cp /path/to/vscode.deb local_assets/packages/

# 将脚本文件放入 scripts 目录
cp /path/to/setup.sh local_assets/scripts/
cp /path/to/config.sh local_assets/scripts/

# 🆕 将 Ubuntu ISO 文件放入 iso 目录（可选）
cp /path/to/ubuntu-24.04.1-desktop-amd64.iso local_assets/iso/
```

#### 3. 配置文件示例
参考 `config-local.json.example` 和 `config-local-iso.json.example`：

```json
{
  "packages": {
    "deb_local_paths": [
      "./local_assets/packages/google-chrome-stable_current_amd64.deb",
      "./local_assets/packages/code_1.84.2-1699528352_amd64.deb"
    ],
    "deb_target_dir": "/opt/packages"
  },
  "first_boot": {
    "scripts": [
      {
        "local_path": "./local_assets/scripts/system-setup.sh",
        "type": "automated"
      }
    ],
    "scripts_target_dir": "/opt/scripts"
  },
  "base_iso_path": "./local_assets/iso/ubuntu-24.04.1-desktop-amd64.iso",
  "base_iso_checksum": "b8f31413336b9393ad5d8ef0282717b2ab19f007df2e9ed5196c13d8f9153c8b"
}
```

#### 4. 运行构建
```bash
./run.sh --use-local-assets config-local.json.example
```

## 📁 项目结构

```
Ubuntu-FAI/
├── 📄 README.md                   # 项目文档
├── 📄 TESTING.md                  # 测试指南
├── 📄 CLAUDE.md                   # 开发指南
├── 🔧 setup-venv.sh               # 虚拟环境设置脚本
├── 🔧 run.sh                      # 主运行脚本
├── 🐍 build.py                    # 构建主程序
├── 📄 requirements.txt            # Python 依赖
├── ⚙️ config.json.example         # 在线模式配置示例
├── ⚙️ config-local.json.example   # 🆕 本地模式配置示例
├── ⚙️ config-local-iso.json.example # 🆕 本地ISO模式配置示例
├── 📂 src/                        # 源代码
│   ├── 📂 config/                 # 配置管理
│   ├── 📂 generators/             # 配置生成器
│   ├── 📂 downloaders/            # 资源下载器
│   ├── 📂 templates/              # Jinja2 模板
│   └── 📂 utils/                  # 工具模块
│       ├── logger.py              # 日志系统
│       └── asset_scanner.py       # 🆕 资源扫描工具
├── 📂 fai_config_base/           # FAI 基础配置
├── 📂 tests/                      # 测试套件
└── 📂 local_assets/              # 🆕 本地资源目录 (用户创建)
    ├── packages/                  # 本地 .deb 文件
    ├── scripts/                   # 本地脚本文件
    └── iso/                       # 🆕 本地 Ubuntu ISO 文件
```

## ⚙️ 配置文件格式

### 硬件配置
```json
{
  "hardware": {
    "vendor": "dell",           // 支持: dell, lenovo, hp, generic
    "target_ssd": true,         // 优先选择 SSD 磁盘
    "disk_size_min_gb": null    // 最小磁盘大小 (GB)
  }
}
```

### 加密配置
```json
{
  "encryption": {
    "enabled": true,
    "passphrase": "MySecureP@ssw0rd123!",
    "cipher": "aes-xts-plain64",        // 支持多种加密算法
    "key_size": 256                     // 256 或 512 位密钥
  }
}
```

### 软件包配置 (支持本地和在线模式)
```json
{
  "packages": {
    "apt_packages": ["curl", "wget", "git", "vim"],
    
    // 在线模式：从 URL 下载
    "deb_urls": [
      "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    ],
    
    // 🆕 本地模式：使用本地文件
    "deb_local_paths": [
      "./local_assets/packages/chrome.deb",
      "./local_assets/packages/vscode.deb"
    ],
    
    // 🆕 目标系统中的安装目录
    "deb_target_dir": "/opt/packages",
    
    "snap_packages": ["discord", "slack"]
  }
}
```

### 首次启动脚本配置
```json
{
  "first_boot": {
    "enabled": true,
    "scripts": [
      {
        // 在线模式
        "url": "https://example.com/script.sh",
        "type": "automated",
        "checksum": "sha256hash..."
      },
      {
        // 🆕 本地模式
        "local_path": "./local_assets/scripts/setup.sh",
        "type": "automated"
      }
    ],
    // 🆕 目标系统中的脚本目录
    "scripts_target_dir": "/opt/scripts",
    "timeout_seconds": 1800
  }
}
```

### 用户配置
```json
{
  "user": {
    "username": "ubuntu",
    "full_name": "System Administrator",
    "password": "SecureUserP@ss123!",
    "ssh_authorized_keys": [
      "ssh-ed25519 AAAAC3... admin@workstation"
    ],
    "sudo_nopasswd": false
  }
}
```

### 🆕 本地 ISO 配置
```json
{
  "base_iso_path": "./local_assets/iso/ubuntu-24.04.1-desktop-amd64.iso",
  "base_iso_url": null,
  "base_iso_checksum": "b8f31413336b9393ad5d8ef0282717b2ab19f007df2e9ed5196c13d8f9153c8b",
  "iso_label": "Ubuntu-24.04-LocalISO"
}
```

**字段说明**：
- `base_iso_path`: 本地 Ubuntu ISO 文件路径（优先级高于 base_iso_url）
- `base_iso_url`: 在线下载 ISO 的 URL（base_iso_path 为空时使用）
- `base_iso_checksum`: ISO 文件的 SHA256 校验和（可选，用于完整性验证）
- `iso_label`: 生成的 ISO 卷标

## 🔄 构建流程

### 阶段说明
1. **配置验证**: 验证 JSON 配置文件的格式和内容
2. **资源准备**: 
   - 在线模式：下载 .deb 包和脚本文件
   - 🆕 本地模式：复制本地文件到缓存目录
   - 🆕 自动扫描模式：扫描并自动发现本地资源
3. **Autoinstall 生成**: 生成 Ubuntu autoinstall 配置
4. **FAI 配置生成**: 生成 FAI 配置空间
5. **首次启动配置**: 生成首次启动服务和脚本
6. **ISO 构建**: 使用 FAI 构建最终 ISO (可选)

### 输出文件
构建完成后，在 `output/` 目录中生成：
- `user-data.yaml` - Ubuntu autoinstall 配置
- `fai-config/` - FAI 配置空间
- `first-boot/` - 首次启动配置
- `*.iso` - 构建的 ISO 文件 (如果执行 FAI 构建)

🆕 **资源扫描模式额外输出**：
- `local_assets/manifest.json` - 资源清单文件 (包含文件信息和哈希值)
- 详细的资源发现和验证日志

## 📊 日志系统

### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息和进度
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 阶段计时
系统记录每个构建阶段的耗时：
- 配置验证
- 🆕 资源扫描 (自动扫描模式) / 资源准备 (本地模式) / 资源下载 (在线模式)
- Autoinstall 生成
- FAI 配置生成
- 首次启动配置生成
- FAI 构建

## 🧪 测试

### 运行测试套件
```bash
# 激活虚拟环境
source ubuntu-fai-venv/bin/activate

# 运行所有测试
pytest

# 运行特定测试
pytest tests/config/
pytest tests/generators/

# 测试覆盖率
pytest --cov=src --cov-report=html
```

### 配置验证测试
```bash
# 测试在线模式配置
python -c "
from src.config.models import BuildConfig
config = BuildConfig.model_validate_json(open('config.json.example').read())
print('在线模式配置验证通过!')
"

# 🆕 测试本地模式配置
python -c "
from src.config.models import BuildConfig
config = BuildConfig.model_validate_json(open('config-local.json.example').read())
print('本地模式配置验证通过!')
"

# 🆕 测试自动资源扫描功能
mkdir -p local_assets/{packages,scripts}
echo "#!/bin/bash" > local_assets/scripts/test.sh
chmod +x local_assets/scripts/test.sh
echo "test package" > local_assets/packages/test.deb

python3 -m src.utils.asset_scanner --base-dir ./local_assets --generate-config
rm -rf local_assets/
```

## 🔧 故障排除

### 常见问题

#### 1. Python 版本不兼容
```bash
python3 --version  # 确认版本 >= 3.9
```

#### 2. 虚拟环境创建失败
```bash
# 安装 venv 模块
sudo apt install python3-venv

# 重新创建环境
rm -rf ubuntu-fai-venv
./setup-venv.sh
```

#### 3. 🆕 本地文件不存在
```bash
# 检查文件路径
ls -la local_assets/packages/
ls -la local_assets/scripts/

# 确认配置文件中的路径正确
cat config-local.json.example
```

#### 4. 配置验证错误
- 检查 JSON 语法是否正确
- 确认必需字段是否存在
- 🆕 确认本地文件路径存在且可读
- 查看日志文件获取详细错误信息

#### 5. 权限问题
```bash
# 确保脚本文件可执行
chmod +x local_assets/scripts/*.sh

# 检查目录权限
ls -la local_assets/
```

#### 6. 🆕 资源扫描问题
```bash
# 检查 local_assets 目录结构
ls -la local_assets/
ls -la local_assets/packages/
ls -la local_assets/scripts/

# 验证文件类型和权限
file local_assets/packages/*.deb 2>/dev/null || echo "没有找到 .deb 文件"
file local_assets/scripts/*.sh 2>/dev/null || echo "没有找到脚本文件"

# 测试资源扫描器
python3 -m src.utils.asset_scanner --base-dir ./local_assets

# 检查扫描结果
cat local_assets/manifest.json 2>/dev/null || echo "清单文件不存在"
```

### 获取详细日志
```bash
# 启用调试模式
./run.sh --debug --skip-fai config.json.example

# 查看构建目录
ls -la output/

# 检查缓存目录
ls -la cache/
```

## 🎯 使用场景

### 企业部署
- 标准化桌面环境
- 预装企业软件
- 统一安全配置
- 批量系统部署

### 开发环境
- 开发工具预装
- 项目环境配置
- 快速环境复制

### 🆕 离线环境
- 🔍 自动发现和管理本地资源
- 使用本地资源构建，无需外网连接
- 安全的内网部署
- 文件完整性自动验证

### 🆕 批量资源管理
- 自动扫描大量 .deb 文件和脚本
- 生成详细的资源清单和哈希值
- 简化资源版本管理和验证

## 📚 详细文档

- [测试指南](TESTING.md) - 完整的测试说明
- [开发指南](CLAUDE.md) - 开发指南和架构说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！请确保：

1. 代码通过所有测试
2. 遵循 PEP8 代码风格  
3. 添加适当的文档和注释
4. 更新相关的测试用例

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [FAI Project](http://fai-project.org/) - Fully Automatic Installation
- [Ubuntu Autoinstall](https://ubuntu.com/server/docs/install/autoinstall) - Ubuntu 自动安装文档
- [Pydantic](https://docs.pydantic.dev/) - 数据验证库
- [Jinja2](https://jinja.palletsprojects.com/) - 模板引擎

---

## 🔍 资源扫描工具详细使用指南

### 命令行选项
```bash
# 基本扫描
python3 -m src.utils.asset_scanner

# 指定扫描目录
python3 -m src.utils.asset_scanner --base-dir ./my-assets

# 生成配置片段
python3 -m src.utils.asset_scanner --generate-config

# 生成配置片段（不包含校验和）
python3 -m src.utils.asset_scanner --generate-config --no-checksums

# 保存资源清单
python3 -m src.utils.asset_scanner --save-manifest

# 验证资源完整性
python3 -m src.utils.asset_scanner --verify-manifest ./local_assets/manifest.json
```

### 扫描输出示例
```
📂 Local Assets Summary (Base: local_assets)
============================================================

📦 DEB Packages (2 found):
  • google-chrome-stable.deb
    Path: local_assets/packages/google-chrome-stable.deb
    Size: 98.50 MB
    MD5:    a1b2c3d4e5f6789...
    SHA256: 9f8e7d6c5b4a3210...

📜 Scripts (1 found):
  • system-setup.sh (✓ Executable)
    Path: local_assets/scripts/system-setup.sh
    Size: 2.3 KB
    MD5:    f1e2d3c4b5a6789...
    SHA256: 8e7d6c5b4a32109...

💿 ISO Files (1 found):
  • ubuntu-24.04.1-desktop-amd64.iso
    Path: local_assets/iso/ubuntu-24.04.1-desktop-amd64.iso
    Size: 5.67 GB
    MD5:    f8e7d6c5b4a32109...
    SHA256: b8f31413336b9393ad5d8ef0282717b2ab19f007df2e9ed5196c13d8f9153c8b

📊 Total: 4 files, 5.77 GB
============================================================
```

### 集成到构建流程
```bash
# 方法1：使用 run.sh 脚本
./run.sh --scan-assets config.json.example

# 方法2：直接使用 build.py
python3 build.py --scan-assets config.json.example

# 方法3：先扫描后构建
python3 -m src.utils.asset_scanner --save-manifest
./run.sh --use-local-assets config-local.json.example
```

---

## 💿 本地 ISO 文件使用指南

### 下载 Ubuntu ISO
```bash
# 下载 Ubuntu 24.04.1 Desktop ISO
wget https://releases.ubuntu.com/24.04/ubuntu-24.04.1-desktop-amd64.iso

# 验证 ISO 完整性（可选但推荐）
echo "b8f31413336b9393ad5d8ef0282717b2ab19f007df2e9ed5196c13d8f9153c8b ubuntu-24.04.1-desktop-amd64.iso" | sha256sum -c
```

### 使用本地 ISO 的三种方式

#### 方式1：自动扫描模式 🆕
```bash
# 1. 准备目录
mkdir -p local_assets/iso

# 2. 放置 ISO 文件
cp ubuntu-24.04.1-desktop-amd64.iso local_assets/iso/

# 3. 自动扫描并构建
./run.sh --scan-assets config.json.example
```

#### 方式2：手动配置模式
```bash
# 1. 创建配置文件
cp config.json.example my-config-iso.json

# 2. 编辑配置文件，添加 ISO 路径
{
  ...
  "base_iso_path": "./ubuntu-24.04.1-desktop-amd64.iso",
  "base_iso_checksum": "b8f31413336b9393ad5d8ef0282717b2ab19f007df2e9ed5196c13d8f9153c8b"
}

# 3. 运行构建
./run.sh my-config-iso.json
```

#### 方式3：使用示例配置
```bash
# 使用预配置的本地 ISO 示例
./run.sh --use-local-assets config-local-iso.json.example
```

### 完全离线构建环境
```bash
# 创建完整的离线构建环境
mkdir -p local_assets/{iso,packages,scripts}

# 放置基础 ISO
cp ubuntu-24.04.1-desktop-amd64.iso local_assets/iso/

# 放置所需的 .deb 包
cp *.deb local_assets/packages/

# 放置自定义脚本
cp *.sh local_assets/scripts/

# 扫描所有资源并构建
./run.sh --scan-assets config.json.example
```

### ISO 验证和故障排除
```bash
# 检查 ISO 文件
file local_assets/iso/*.iso

# 验证 ISO 完整性
python3 -c "
import hashlib
with open('local_assets/iso/ubuntu-24.04.1-desktop-amd64.iso', 'rb') as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f'SHA256: {sha256}')
"

# 扫描并生成配置片段
python3 -m src.utils.asset_scanner --base-dir ./local_assets --generate-config
```

---

🎯 **目标**: 简化 Ubuntu 定制 ISO 的创建过程，提供可重现的企业级部署解决方案，支持在线资源下载、本地资源管理、自动资源扫描和完全离线构建四种模式。