# Ubuntu FAI Build System - Conda 环境设置指南

本项目支持使用 conda 来管理 Python 运行环境，提供更好的依赖管理和环境隔离。

## 📋 前提条件

### 安装 Miniconda 或 Anaconda

如果您还没有安装 conda，请选择其中一种方式：

**选项 1: Miniconda (推荐，轻量级)**
```bash
# macOS
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Linux
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

**选项 2: Anaconda (完整版)**
- 访问 https://www.anaconda.com/download
- 下载并安装适合您系统的版本

## 🚀 快速开始

### 1. 自动环境设置（推荐）

使用我们提供的自动化脚本：

```bash
# 创建 conda 环境
./setup-conda-env.sh

# 检查环境状态
./setup-conda-env.sh --check

# 重新创建环境（如果需要）
./setup-conda-env.sh --recreate

# 更新环境
./setup-conda-env.sh --update
```

### 2. 手动环境设置

如果您喜欢手动控制：

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate ubuntu-fai

# 验证安装
python -c "import pydantic, jinja2, yaml; print('所有包安装成功！')"
```

## 💻 开发工作流

### 本地开发

```bash
# 激活环境
conda activate ubuntu-fai

# 运行构建（本地环境）
./run-conda.sh --local config.json.example

# 运行测试
pytest tests/ -v

# 代码格式化
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
ruff check src/ tests/
```

### Docker 开发

```bash
# 构建 conda 版本的 Docker 镜像
./run-conda.sh --build config.json.example

# 运行构建（Docker 环境）
./run-conda.sh config.json.example

# 调试模式
./run-conda.sh --debug config.json.example
```

## 🔧 环境管理

### 添加新依赖

1. 编辑 `environment.yml`：
```yaml
dependencies:
  # 现有依赖...
  - your-new-package=1.0.*
```

2. 更新环境：
```bash
./setup-conda-env.sh --update
```

### 环境文件结构

```
Ubuntu-FAI/
├── environment.yml          # Conda 环境配置
├── setup-conda-env.sh      # 环境设置脚本
├── run-conda.sh            # Conda 版本运行脚本
├── Dockerfile.conda        # Conda 版本 Docker 文件
├── requirements.txt        # pip 依赖（保留兼容性）
└── Dockerfile              # 标准 Docker 文件（原版）
```

## 🐳 Docker 使用

### 构建镜像

```bash
# 使用 conda 版本构建
docker build -f Dockerfile.conda -t ubuntu-fai-conda .

# 或使用脚本
./run-conda.sh --build config.json.example
```

### 运行容器

```bash
# 基本运行
./run-conda.sh config.json.example

# 自定义输出目录
./run-conda.sh --output-dir /path/to/output config.json

# 调试模式
./run-conda.sh --debug config.json.example
```

## 🛠️ 故障排除

### 常见问题

**问题: conda 命令未找到**
```bash
# 解决方案: 初始化 conda
conda init bash
source ~/.bashrc
```

**问题: 环境创建失败**
```bash
# 解决方案: 清理并重试
conda clean --all
./setup-conda-env.sh --recreate
```

**问题: 包冲突**
```bash
# 解决方案: 检查环境文件
conda env export -n ubuntu-fai
# 根据输出调整 environment.yml
```

### 环境验证

```bash
# 检查环境
conda info --envs

# 检查包列表
conda list -n ubuntu-fai

# 验证关键功能
conda run -n ubuntu-fai python -c "
import sys
print(f'Python: {sys.version}')
import pydantic, jinja2, yaml, requests
print('✓ 所有关键包可用')
"
```

## 📊 性能优化

### Conda 配置优化

```bash
# 添加 conda-forge 频道
conda config --add channels conda-forge

# 启用严格频道优先级
conda config --set channel_priority strict

# 启用 mamba 求解器（更快）
conda install -n base conda-libmamba-solver
conda config --set solver libmamba
```

### 构建缓存

```bash
# 使用构建缓存
./run-conda.sh config.json  # 默认使用缓存

# 强制重新构建
./run-conda.sh --build --no-cache config.json
```

## 🔄 与现有工具的兼容性

项目同时支持两种环境管理方式：

1. **Conda 环境** (推荐)
   - `environment.yml`
   - `./run-conda.sh`
   - `Dockerfile.conda`

2. **传统 pip 环境** (兼容性)
   - `requirements.txt`
   - `./run.sh`
   - `Dockerfile`

您可以根据需要选择使用哪种方式，两者功能完全相同。

## 🆘 获取帮助

```bash
# 查看设置脚本帮助
./setup-conda-env.sh --help

# 查看运行脚本帮助
./run-conda.sh --help

# 检查环境状态
./setup-conda-env.sh --check
```

如果遇到问题，请检查：
1. conda 是否正确安装
2. 环境是否正确创建
3. 所有依赖是否安装完成
4. Docker 是否运行（如果使用 Docker 模式）