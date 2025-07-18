#!/bin/bash

# Ubuntu FAI Build System - Virtual Environment Setup Script
# 创建和配置 Python 虚拟环境

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="ubuntu-fai-venv"
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# 颜色输出函数
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."

    # 检查 Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装。请安装 Python 3.9 或更高版本。"
        exit 1
    fi

    # 检查 Python 版本
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.9"

    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        log_error "Python 版本 $PYTHON_VERSION 不满足要求。需要 Python $REQUIRED_VERSION 或更高版本。"
        exit 1
    fi

    log_success "Python 版本检查通过: $(python3 --version)"

    # 检查 venv 模块
    if ! python3 -c "import venv" 2>/dev/null; then
        log_error "Python venv 模块未安装。请安装: sudo apt install python3-venv"
        exit 1
    fi

    # 检查 pip
    if ! python3 -c "import pip" 2>/dev/null; then
        log_error "pip 未安装。请安装: sudo apt install python3-pip"
        exit 1
    fi

    log_success "系统要求检查通过"
}

# 创建虚拟环境
create_virtual_environment() {
    log_info "创建 Python 虚拟环境: $VENV_NAME"

    # 如果虚拟环境已存在，询问是否重新创建
    if [[ -d "$VENV_PATH" ]]; then
        log_warning "虚拟环境已存在: $VENV_PATH"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "删除现有虚拟环境..."
            rm -rf "$VENV_PATH"
        else
            log_info "使用现有虚拟环境"
            return 0
        fi
    fi

    # 创建虚拟环境
    python3 -m venv "$VENV_PATH"

    if [[ ! -d "$VENV_PATH" ]]; then
        log_error "虚拟环境创建失败"
        exit 1
    fi

    log_success "虚拟环境创建成功: $VENV_PATH"
}

# 激活虚拟环境并安装依赖
install_dependencies() {
    log_info "激活虚拟环境并安装依赖..."

    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"

    # 升级 pip
    log_info "升级 pip..."
    python -m pip install --upgrade pip

    # 检查 requirements.txt 文件
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "requirements.txt 文件不存在: $REQUIREMENTS_FILE"
        exit 1
    fi

    # 安装依赖
    log_info "安装 Python 依赖包..."
    pip install -r "$REQUIREMENTS_FILE"

    log_success "依赖安装完成"
}

# 验证安装
verify_installation() {
    log_info "验证安装..."

    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"

    # 检查关键包
    local packages=("pydantic" "jinja2" "pyyaml" "requests" "pytest")

    for package in "${packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            log_success "✓ $package"
        else
            log_error "✗ $package 安装失败"
            exit 1
        fi
    done

    log_success "所有依赖包验证通过"
}

# 创建激活脚本
create_activation_script() {
    local activate_script="$SCRIPT_DIR/activate-venv.sh"

    log_info "创建激活脚本: $activate_script"

    cat > "$activate_script" << 'EOF'
#!/bin/bash

# Ubuntu FAI Build System - Virtual Environment Activation
# 激活 Python 虚拟环境

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/ubuntu-fai-venv"

if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "\033[0;31m[ERROR]\033[0m 虚拟环境不存在: $VENV_PATH"
    echo -e "\033[0;34m[INFO]\033[0m 请先运行: ./setup-venv.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_PATH/bin/activate"

echo -e "\033[0;32m[SUCCESS]\033[0m 虚拟环境已激活: ubuntu-fai-venv"
echo -e "\033[0;34m[INFO]\033[0m 使用 'deactivate' 命令退出虚拟环境"
echo -e "\033[0;34m[INFO]\033[0m 运行构建: python build.py config.json.example"

# 启动新的 shell 会话
exec "$SHELL"
EOF

    chmod +x "$activate_script"
    log_success "激活脚本创建完成"
}

# 主函数
main() {
    log_info "Ubuntu FAI Build System - 虚拟环境设置"
    log_info "========================================="

    check_system_requirements
    create_virtual_environment
    install_dependencies
    verify_installation
    create_activation_script

    log_success "虚拟环境设置完成!"
    echo
    log_info "使用方法:"
    log_info "1. 激活虚拟环境: source ubuntu-fai-venv/bin/activate"
    log_info "2. 或使用便捷脚本: ./activate-venv.sh"
    log_info "3. 运行构建: python build.py config.json.example"
    log_info "4. 退出虚拟环境: deactivate"
}

# 错误处理
trap 'log_error "脚本执行失败"; exit 1' ERR

# 运行主函数
main "$@"