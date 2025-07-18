# Ubuntu FAI Build System

🚀 **自动化 Ubuntu 24.04 Desktop ISO 构建系统**

使用 FAI (Fully Automatic Installation) 和 conda 环境管理的现代化 Ubuntu 定制 ISO 构建工具。

## 🌟 特性

- **🐍 Conda 环境管理**: 使用 conda 管理 Python 依赖，支持本地和 Docker 两种运行模式
- **⚙️ 智能配置验证**: 基于 Pydantic v2 的强类型配置验证和错误检查
- **🎨 模板化生成**: 使用 Jinja2 模板生成 autoinstall 和 FAI 配置
- **🔒 加密支持**: 内置 LUKS 磁盘加密配置，支持多种加密算法
- **🖥️ 硬件适配**: 支持 Dell、Lenovo、HP 等主流硬件厂商的专用配置
- **📦 软件包管理**: 支持 APT、Snap、DEB 包的自动安装
- **🔧 首次启动脚本**: 自动化首次启动配置和软件安装
- **📋 详细日志**: 完整的构建过程日志记录和错误追踪

## 🛠️ 系统要求

### 必需依赖
- **Python 3.11+**
- **Conda/Miniconda** (推荐使用 Miniforge)
- **Docker** (可选，用于容器化构建)

### 平台支持
- ✅ macOS (ARM64/Intel)
- ✅ Linux (x86_64/ARM64)
- ⚠️ Windows (通过 WSL2)

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd Ubuntu-FAI
```

### 2. 设置 Conda 环境
```bash
./setup-conda-env.sh
```

### 3. 验证安装
```bash
./run-conda.sh --local --skip-fai config.json.example
```

### 4. 创建自定义配置
```bash
cp config.json.example my-config.json
# 编辑 my-config.json 以满足您的需求
```

### 5. 构建 ISO (生成配置文件)
```bash
./run-conda.sh --local --skip-fai my-config.json
```

## 📁 项目结构

```
Ubuntu-FAI/
├── build.py                    # 主构建脚本
├── run-conda.sh               # Conda 环境运行脚本
├── setup-conda-env.sh         # Conda 环境设置脚本
├── environment.yml            # Conda 环境定义
├── config.json.example        # 配置文件示例
├── config-working.json        # 测试配置文件
│
├── src/                       # 源代码目录
│   ├── config/               # 配置管理
│   │   ├── models.py         # Pydantic 数据模型
│   │   └── validator.py      # 配置验证器
│   ├── generators/           # 配置生成器
│   │   ├── autoinstall.py    # Ubuntu autoinstall 生成
│   │   ├── fai_config.py     # FAI 配置生成
│   │   └── first_boot.py     # 首次启动脚本生成
│   ├── downloaders/          # 下载管理器
│   │   ├── packages.py       # 软件包下载
│   │   └── scripts.py        # 脚本下载
│   └── templates/            # Jinja2 模板
│       ├── user-data.yaml.j2 # Autoinstall 模板
│       └── user-data-simple.yaml.j2 # 简化模板
│
├── fai_config_base/          # FAI 基础配置
├── first_boot_scripts/       # 首次启动脚本
├── output/                   # 生成的配置文件
├── cache/                    # 下载缓存
└── logs/                     # 构建日志
```

## ⚙️ 配置文件格式

```json
{
  "hardware": {
    "vendor": "dell",           // 硬件厂商: dell, lenovo, hp, generic
    "target_ssd": true,         // 是否针对 SSD 优化
    "disk_size_min_gb": null    // 最小磁盘大小 (GB)
  },
  "encryption": {
    "enabled": true,            // 是否启用 LUKS 加密
    "passphrase": "your-secure-passphrase",
    "cipher": "aes-xts-plain64", // 加密算法
    "key_size": 256             // 密钥长度
  },
  "packages": {
    "apt_packages": ["git", "curl", "vim"],  // APT 软件包
    "deb_urls": [],                          // DEB 包下载链接
    "snap_packages": ["code"]                // Snap 软件包
  },
  "user": {
    "username": "ubuntu",       // 用户名
    "full_name": "Ubuntu User", // 全名
    "password": "password",     // 密码
    "ssh_authorized_keys": [],  // SSH 公钥
    "sudo_nopasswd": false      // 是否免密 sudo
  },
  "first_boot": {
    "enabled": true,            // 是否启用首次启动脚本
    "scripts": []               // 首次启动脚本列表
  },
  "network": {
    "dhcp": true,               // 是否使用 DHCP
    "hostname": "ubuntu-desktop" // 主机名
  }
}
```

## 🔧 使用方法

### 本地 Conda 环境 (推荐)
```bash
# 仅生成配置文件 (跳过 FAI 构建)
./run-conda.sh --local --skip-fai config.json

# 包含下载但跳过 FAI 构建
./run-conda.sh --local --skip-fai config.json

# 跳过下载和 FAI 构建 (使用缓存)
./run-conda.sh --local --skip-downloads --skip-fai config.json

# 启用调试模式
./run-conda.sh --local --debug --skip-fai config.json
```

### Docker 环境
```bash
# 构建 Docker 镜像
./run-conda.sh --build config.json

# 使用现有镜像运行
./run-conda.sh config.json

# 强制重建镜像
./run-conda.sh --build --no-cache config.json
```

### 命令行参数
```bash
用法: ./run-conda.sh [选项] <config.json> [构建参数...]

选项:
  -h, --help              显示帮助信息
  -b, --build             强制重新构建 Docker 镜像
  -c, --clean             清理容器和镜像
  -d, --debug             启用调试模式
  --no-cache              构建镜像时不使用缓存
  --output-dir DIR        指定输出目录 (默认: ./output)
  --local                 使用本地 conda 环境

构建参数:
  --skip-downloads        跳过资产下载
  --skip-fai              跳过 FAI 构建过程
  --cache-dir DIR         缓存目录路径
  --debug                 启用调试日志
```

## 📊 日志系统

系统提供全面的多级别、多格式日志记录：

### 日志级别
- **DEBUG**: 详细的调试信息 (包括构建阶段时间)
- **INFO**: 一般信息和进度 (构建状态、配置验证)
- **WARNING**: 警告信息 (配置警告、性能提示)
- **ERROR**: 错误信息 (构建失败、验证错误)

### 日志输出格式
- **控制台日志**: 彩色格式，实时显示构建进程
- **文件日志**: 详细格式，包含时间戳、模块、函数信息
- **JSON 日志**: 机器可读格式，便于分析和监控
- **错误日志**: 单独的错误和警告日志文件

### 日志文件位置
```
logs/
├── build.log              # 主构建日志 (详细信息)
├── error.log             # 错误和警告日志
├── build.json            # JSON 格式日志 (机器可读)
└── session_YYYYMMDD_HHMMSS.json  # 会话摘要
```

### 构建阶段追踪
系统自动记录各个构建阶段的执行时间：
- **配置验证** (config_validation)
- **资产下载** (asset_download)  
- **Autoinstall 生成** (autoinstall_generation)
- **FAI 配置生成** (fai_generation)
- **首次启动配置** (first_boot_generation)
- **FAI 构建** (fai_build)

### 查看日志
```bash
# 查看最新构建日志 (彩色输出)
tail -f logs/build.log

# 查看错误日志
cat logs/error.log

# 查看 JSON 格式日志
jq '.' logs/build.json

# 启用详细调试模式
./run-conda.sh --local --debug --skip-fai config.json

# 监控构建进度 (实时)
./run-conda.sh --local --skip-fai config.json | grep "阶段"
```

### 日志分析示例
```bash
# 分析构建时间
grep "耗时" logs/build.log

# 查看配置验证结果
grep "配置验证" logs/build.log

# 检查模板生成状态
grep "模板生成" logs/build.log

# 分析 JSON 日志中的构建阶段
jq '.build_phase' logs/build.json | sort | uniq -c
```

## 🎯 输出文件

构建完成后，输出目录包含：

```
output/
├── user-data.yaml              # Ubuntu autoinstall 配置
├── fai-config/                 # FAI 配置空间
│   ├── class/                  # FAI 类脚本
│   ├── disk_config/            # 磁盘配置
│   ├── package_config/         # 软件包配置
│   └── scripts/                # 安装脚本
└── first-boot/                 # 首次启动配置
    ├── first-boot.service      # Systemd 服务
    ├── first-boot.sh           # 启动脚本
    └── scripts/                # 自定义脚本
```

## 🛠️ 故障排除

### 常见问题

#### 1. Conda 环境创建失败
```bash
# 删除现有环境并重新创建
conda env remove -n ubuntu-fai
./setup-conda-env.sh
```

#### 2. 配置验证错误
```bash
# 检查配置文件格式
python -m json.tool config.json

# 查看详细验证错误
./run-conda.sh --local --debug --skip-fai config.json
```

#### 3. 权限问题
```bash
# 确保脚本有执行权限
chmod +x run-conda.sh setup-conda-env.sh

# 检查输出目录权限
ls -la output/
```

#### 4. Docker 构建失败 (ARM64)
```bash
# 在 Apple Silicon Mac 上优先使用本地模式
./run-conda.sh --local --skip-fai config.json

# 如果需要 Docker，确保 Docker Desktop 支持 ARM64
docker buildx ls
```

### 调试技巧

1. **启用详细日志**:
   ```bash
   ./run-conda.sh --local --debug --skip-fai config.json
   ```

2. **检查生成的配置**:
   ```bash
   # 验证 YAML 语法
   python -c "import yaml; yaml.safe_load(open('output/user-data.yaml'))"
   ```

3. **测试配置验证**:
   ```bash
   # 单独测试配置加载
   conda run -n ubuntu-fai python -c "
   from src.config.models import BuildConfig
   import json
   with open('config.json') as f:
       config = BuildConfig(**json.load(f))
   print('配置验证成功')
   "
   ```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd Ubuntu-FAI

# 设置开发环境
./setup-conda-env.sh

# 运行测试
conda run -n ubuntu-fai python -m pytest tests/

# 代码格式化
conda run -n ubuntu-fai black src/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- **GitHub Issues**: [报告问题](../../issues)
- **讨论区**: [社区讨论](../../discussions)
- **文档**: [详细文档](docs/)

## 🔗 相关资源

- [FAI 官方文档](https://fai-project.org/)
- [Ubuntu Autoinstall](https://ubuntu.com/server/docs/install/autoinstall)
- [Conda 用户指南](https://docs.conda.io/en/latest/)

---

**⭐ 如果这个项目对您有帮助，请给它一个星标！**