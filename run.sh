#!/bin/bash

# Ubuntu FAI Build System - 构建运行脚本
# 使用 Python 虚拟环境运行 Ubuntu FAI 构建系统

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="ubuntu-fai-venv"
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"

# 默认参数
CONFIG_FILE=""
SKIP_DOWNLOADS=false
SKIP_FAI=false
DEBUG=false
HELP=false

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

# 显示帮助信息
show_help() {
    cat << EOF
Ubuntu FAI Build System - 构建运行脚本

用法: $0 [选项] <配置文件>

选项:
  --skip-downloads    跳过资源下载阶段
  --skip-fai         跳过 FAI ISO 构建阶段
  --debug            启用调试模式
  --help             显示此帮助信息

参数:
  <配置文件>         构建配置文件路径 (例如: config.json.example)

示例:
  $0 config.json.example
  $0 --skip-downloads config.json.example
  $0 --debug --skip-fai config.json.example

注意:
  - 请确保已经运行 ./setup-venv.sh 创建虚拟环境
  - 构建需要在 Ubuntu 环境中运行
  - 使用 --skip-fai 仅生成配置文件而不构建 ISO
EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-downloads)
                SKIP_DOWNLOADS=true
                shift
                ;;
            --skip-fai)
                SKIP_FAI=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --help|-h)
                HELP=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "$CONFIG_FILE" ]]; then
                    CONFIG_FILE="$1"
                else
                    log_error "多余的参数: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [[ "$HELP" == true ]]; then
        show_help
        exit 0
    fi

    if [[ -z "$CONFIG_FILE" ]]; then
        log_error "缺少配置文件参数"
        show_help
        exit 1
    fi
}

# 检查虚拟环境
check_virtual_environment() {
    log_info "检查 Python 虚拟环境..."
    
    if [[ ! -d "$VENV_PATH" ]]; then
        log_error "虚拟环境不存在: $VENV_PATH"
        log_info "请先运行: ./setup-venv.sh"
        exit 1
    fi
    
    if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
        log_error "虚拟环境激活脚本不存在: $VENV_PATH/bin/activate"
        log_info "请重新运行: ./setup-venv.sh"
        exit 1
    fi
    
    log_success "虚拟环境检查通过: $VENV_NAME"
}

# 验证配置文件
validate_config() {
    log_info "验证配置文件..."

    if [[ -z "$CONFIG_FILE" ]]; then
        log_error "未指定配置文件"
        exit 1
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi

    if [[ ! -r "$CONFIG_FILE" ]]; then
        log_error "配置文件不可读: $CONFIG_FILE"
        exit 1
    fi

    # 获取绝对路径
    CONFIG_FILE=$(realpath "$CONFIG_FILE")
    log_success "使用配置文件: $CONFIG_FILE"
}

# 准备输出目录
prepare_output_dir() {
    local output_dir

    # 确定输出目录路径
    output_dir="$SCRIPT_DIR/output"
    
    # 检查输出目录
    if [[ ! -d "$output_dir" ]]; then
        log_info "创建输出目录: $output_dir"
        mkdir -p "$output_dir"
    fi
    
    if [[ ! -w "$output_dir" ]]; then
        log_error "输出目录不可写: $output_dir"
        exit 1
    fi
    
    log_success "使用输出目录: $output_dir"
}

# 构建构建参数
build_build_args() {
    local args=()

    # 添加配置文件参数
    args+=("$CONFIG_FILE")

    # 添加可选参数
    if [[ "$SKIP_DOWNLOADS" == true ]]; then
        args+=("--skip-downloads")
    fi

    if [[ "$SKIP_FAI" == true ]]; then
        args+=("--skip-fai")
    fi
    
    if [[ "$DEBUG" == true ]]; then
        args+=("--debug")
    fi

    echo "${args[@]}"
}

# 运行构建
run_build() {
    log_info "激活虚拟环境并运行构建..."
    
    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"
    
    # 检查 Python 解释器
    if ! command -v python &> /dev/null; then
        log_error "虚拟环境中的 Python 解释器不可用"
        exit 1
    fi
    
    # 构建参数
    local build_args
    build_args=($(build_build_args))

    log_info "运行构建命令: python build.py ${build_args[*]}"

    # 运行构建
    if python build.py "${build_args[@]}"; then
        log_success "构建完成成功"
        log_info "检查输出目录: $SCRIPT_DIR/output"
    else
        log_error "构建失败"
        exit 1
    fi
}

# 清理函数
cleanup() {
    if [[ "${VIRTUAL_ENV:-}" ]]; then
        deactivate 2>/dev/null || true
    fi
}

# 主函数
main() {
    # 显示调试状态
    if [[ "$DEBUG" == true ]]; then
        log_info "调试模式已启用"
    fi
    
    # 设置错误处理
    trap 'log_warning "用户中断"; exit 130' INT TERM
    trap cleanup EXIT
    
    check_virtual_environment
    validate_config
    prepare_output_dir
    run_build
}

# 解析参数并运行
parse_arguments "$@"
main