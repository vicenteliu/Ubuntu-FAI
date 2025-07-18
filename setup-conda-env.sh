#!/bin/bash
# Ubuntu FAI Build System - Conda 环境设置脚本
# 本地开发环境初始化

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="ubuntu-fai"
ENV_FILE="$SCRIPT_DIR/environment.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用说明
usage() {
    cat << EOF
Ubuntu FAI Build System - Conda 环境设置

用法:
    $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -r, --recreate      删除现有环境并重新创建
    -u, --update        更新现有环境
    -c, --check         检查环境状态

示例:
    $0                  # 创建环境（如果不存在）
    $0 --recreate       # 强制重新创建环境
    $0 --update         # 更新现有环境的包

注意:
    - 需要预先安装 conda 或 miniconda
    - 环境名称: $ENV_NAME
    - 配置文件: $ENV_FILE

EOF
}

# 检查 conda 是否可用
check_conda() {
    if ! command -v conda &> /dev/null; then
        log_error "conda 未找到。请先安装 Miniconda 或 Anaconda"
        log_info "下载地址: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi

    # 初始化 conda（如果需要）
    if ! conda info --envs &> /dev/null; then
        log_info "初始化 conda..."
        conda init bash
        log_warning "请重新启动终端或运行 'source ~/.bashrc' 后重试"
        exit 1
    fi
}

# 检查环境文件
check_environment_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "环境文件不存在: $ENV_FILE"
        exit 1
    fi

    log_info "使用环境文件: $ENV_FILE"
}

# 检查环境是否存在
environment_exists() {
    conda env list | grep -q "^$ENV_NAME "
}

# 创建环境
create_environment() {
    log_info "创建 conda 环境: $ENV_NAME"
    
    if conda env create -f "$ENV_FILE"; then
        log_success "环境创建成功: $ENV_NAME"
    else
        log_error "环境创建失败"
        exit 1
    fi
}

# 更新环境
update_environment() {
    log_info "更新 conda 环境: $ENV_NAME"
    
    if conda env update -f "$ENV_FILE"; then
        log_success "环境更新成功: $ENV_NAME"
    else
        log_error "环境更新失败"
        exit 1
    fi
}

# 删除环境
remove_environment() {
    log_info "删除现有环境: $ENV_NAME"
    
    if conda env remove -n "$ENV_NAME"; then
        log_success "环境删除成功: $ENV_NAME"
    else
        log_warning "环境删除失败或不存在"
    fi
}

# 验证环境
validate_environment() {
    log_info "验证环境: $ENV_NAME"
    
    # 激活环境并检查关键包
    if conda run -n "$ENV_NAME" python -c "
import sys
print(f'Python version: {sys.version}')

# 检查关键包
try:
    import pydantic
    import jinja2
    import yaml
    import requests
    print('✓ 所有关键包导入成功')
except ImportError as e:
    print(f'✗ 包导入失败: {e}')
    sys.exit(1)
"; then
        log_success "环境验证通过"
    else
        log_error "环境验证失败"
        exit 1
    fi
}

# 显示环境信息
show_environment_info() {
    log_info "环境信息:"
    echo "  名称: $ENV_NAME"
    echo "  位置: $(conda info --envs | grep "^$ENV_NAME " | awk '{print $2}')"
    echo "  Python 版本: $(conda run -n "$ENV_NAME" python --version)"
    echo ""
    log_info "激活环境:"
    echo "  conda activate $ENV_NAME"
    echo ""
    log_info "验证安装:"
    echo "  python -c \"import pydantic, jinja2, yaml; print('所有包正常')\""
}

# 主函数
main() {
    local recreate=false
    local update=false
    local check_only=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -r|--recreate)
                recreate=true
                shift
                ;;
            -u|--update)
                update=true
                shift
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                usage
                exit 1
                ;;
        esac
    done

    # 检查依赖
    check_conda
    check_environment_file

    # 仅检查模式
    if [[ "$check_only" == "true" ]]; then
        if environment_exists; then
            log_success "环境 $ENV_NAME 存在"
            validate_environment
            show_environment_info
        else
            log_warning "环境 $ENV_NAME 不存在"
            exit 1
        fi
        exit 0
    fi

    # 重新创建模式
    if [[ "$recreate" == "true" ]]; then
        if environment_exists; then
            remove_environment
        fi
        create_environment
        validate_environment
        show_environment_info
        exit 0
    fi

    # 更新模式
    if [[ "$update" == "true" ]]; then
        if environment_exists; then
            update_environment
            validate_environment
            show_environment_info
        else
            log_error "环境 $ENV_NAME 不存在，无法更新"
            log_info "使用 '$0' 创建环境"
            exit 1
        fi
        exit 0
    fi

    # 默认模式：创建（如果不存在）
    if environment_exists; then
        log_warning "环境 $ENV_NAME 已存在"
        log_info "使用 '$0 --update' 更新或 '$0 --recreate' 重新创建"
        validate_environment
        show_environment_info
    else
        create_environment
        validate_environment
        show_environment_info
    fi
}

# 运行主函数
main "$@"