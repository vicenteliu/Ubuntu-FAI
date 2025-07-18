# Ubuntu FAI Build System

🚀 **自动化 Ubuntu 24.04 Desktop ISO 构建系统**

使用 FAI (Fully Automatic Installation) 和 Python 虚拟环境的现代化 Ubuntu 定制 ISO 构建工具。

## 🌟 特性

- **🐍 Python 虚拟环境**: 使用 Python venv 管理依赖，确保环境隔离和可重现性
- **⚙️ 智能配置验证**: 基于 Pydantic v2 的强类型配置验证和错误检查
- **🎨 模板化生成**: 使用 Jinja2 模板生成 autoinstall 和 FAI 配置
- **🔒 加密支持**: 内置 LUKS 磁盘加密配置，支持多种加密算法
- **🖥️ 硬件适配**: 支持 Dell、Lenovo、HP 等主流硬件厂商的专用配置
- **📦 软件包管理**: 支持 APT、Snap、DEB 包的自动安装
- **🔧 首次启动脚本**: 自动化首次启动配置和软件安装
- **📊 增强日志系统**: 多级别日志记录，支持控制台、文件和 JSON 格式输出
- **⏱️ 构建时间追踪**: 详细的阶段计时和性能分析

## 🛠️ 系统要求

### 必需依赖
- **Ubuntu 24.04 LTS** (推荐)
- **Python 3.9+**
- **python3-venv** (虚拟环境模块)
- **FAI** (用于 ISO 构建，可选)

### 系统包安装
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip git

# FAI 工具 (用于实际 ISO 构建)
sudo apt install fai-server fai-setup-storage
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

### 3. 激活虚拟环境
```bash
# 方法 1: 手动激活
source ubuntu-fai-venv/bin/activate

# 方法 2: 使用便捷脚本
./activate-venv.sh
```

### 4. 验证安装
```bash
./run.sh --skip-fai config.json.example
```

### 5. 创建自定义配置
```bash
cp config.json.example my-config.json
# 编辑 my-config.json 根据需要自定义配置
```

## 📋 使用方法

### 基本构建命令
```bash
# 完整构建 (生成配置 + 构建 ISO)
./run.sh my-config.json

# 仅生成配置文件
./run.sh --skip-fai my-config.json

# 跳过下载 (用于测试)
./run.sh --skip-downloads --skip-fai my-config.json

# 调试模式
./run.sh --debug --skip-fai my-config.json
```

### 命令行选项
- `--skip-downloads`: 跳过资源下载阶段
- `--skip-fai`: 跳过 FAI ISO 构建阶段
- `--debug`: 启用调试模式，显示详细日志
- `--help`: 显示帮助信息

## 📁 项目结构

```
Ubuntu-FAI/
├── 📄 README.md                   # 项目文档
├── 📄 TESTING.md                  # 测试指南
├── 🔧 setup-venv.sh               # 虚拟环境设置脚本
├── 🔧 activate-venv.sh            # 虚拟环境激活脚本
├── 🔧 run.sh                      # 主运行脚本
├── 🐍 build.py                    # 构建主程序
├── 📄 requirements.txt            # Python 依赖
├── ⚙️ config.json.example         # 配置示例
├── 📂 src/                        # 源代码
│   ├── 📂 config/                 # 配置管理
│   ├── 📂 generators/             # 配置生成器
│   ├── 📂 downloaders/            # 资源下载器
│   ├── 📂 templates/              # Jinja2 模板
│   └── 📂 utils/                  # 工具模块
├── 📂 fai_config_base/           # FAI 基础配置
├── 📂 output/                     # 构建输出
├── 📂 logs/                       # 日志文件
└── 📂 tests/                      # 测试套件
```

## ⚙️ 配置文件格式

配置文件使用 JSON 格式，包含以下主要部分：

### 硬件配置
```json
{
  "hardware": {
    "vendor": "dell",
    "target_ssd": true,
    "disk_size_min_gb": null
  }
}
```

### 加密配置
```json
{
  "encryption": {
    "enabled": true,
    "passphrase": "MySecureP@ssw0rd123!",
    "cipher": "aes-xts-plain64",
    "key_size": 256
  }
}
```

### 软件包配置
```json
{
  "packages": {
    "apt_packages": ["curl", "wget", "git", "vim"],
    "deb_urls": [
      "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    ],
    "snap_packages": ["discord", "slack"]
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

## 📊 日志系统

系统提供多级别的日志记录：

### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息和进度
- **WARNING**: 警告信息
- **ERROR**: 错误信息

### 日志输出格式
- **控制台**: 彩色格式化输出
- **文件**: 标准格式，保存到 `logs/build.log`
- **JSON**: 结构化格式，保存到 `logs/build.json`

### 阶段计时
系统会记录每个构建阶段的耗时：
- 配置验证
- 资源下载
- Autoinstall 生成
- FAI 配置生成
- 首次启动配置生成

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
```

### 配置验证测试
```bash
# 测试配置验证
python -c "
from src.config.models import BuildConfig
config = BuildConfig.from_file('config.json.example')
print('配置验证通过!')
"
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

#### 3. 依赖安装失败
```bash
# 升级 pip
source ubuntu-fai-venv/bin/activate
python -m pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt
```

#### 4. 配置验证错误
- 检查 JSON 语法是否正确
- 确认必需字段是否存在
- 查看日志文件获取详细错误信息

#### 5. 资源下载失败
```bash
# 跳过下载进行测试
./run.sh --skip-downloads --skip-fai config.json.example
```

### 获取详细日志
```bash
# 启用调试模式
./run.sh --debug --skip-fai config.json.example

# 查看日志文件
tail -f logs/build.log
```

## 📚 详细文档

- [测试指南](TESTING.md) - 完整的测试说明
- [项目规划](CLAUDE.md) - 开发指南和架构说明

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
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库
- [Jinja2](https://jinja.palletsprojects.com/) - 模板引擎

---

🎯 **目标**: 简化 Ubuntu 定制 ISO 的创建过程，提供可重现的企业级部署解决方案。