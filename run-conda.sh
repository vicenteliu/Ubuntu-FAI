#!/bin/bash
# Ubuntu FAI Build System Docker Runner with Conda Support
# 使用 conda 环境的 Docker 构建和执行脚本

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="ubuntu-fai-conda"
IMAGE_TAG="latest"
CONTAINER_NAME="ubuntu-fai-conda-build"
DOCKERFILE="Dockerfile.conda"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
Ubuntu FAI Build System Docker Runner (Conda 版本)

用法:
    $0 [选项] <config.json> [构建参数...]

选项:
    -h, --help              显示此帮助信息
    -b, --build             强制重新构建 Docker 镜像
    -c, --clean             清理容器和镜像
    -d, --debug             启用调试模式（详细输出）
    --no-cache              构建镜像时不使用缓存
    --output-dir DIR        指定输出目录（默认: ./output）
    --local                 使用本地 conda 环境（不使用 Docker）

示例:
    $0 config.json.example                    # 使用示例配置构建 ISO
    $0 --build config.json.example           # 重新构建镜像后构建
    $0 --local config.json.example           # 使用本地 conda 环境
    $0 --output-dir /tmp/iso config.json     # 自定义输出目录
    $0 --debug config.json                   # 启用详细日志

注意:
    - Docker 必须已安装并运行（除非使用 --local）
    - 配置文件必须存在且可读
    - 输出目录会自动创建（如果不存在）
    - 使用 --local 时需要先运行 ./setup-conda-env.sh

EOF
}

# 解析命令行参数
FORCE_BUILD=false
CLEAN=false
DEBUG=false
NO_CACHE=false
USE_LOCAL=false
OUTPUT_DIR="$SCRIPT_DIR/output"
CONFIG_FILE=""
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build)
            FORCE_BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --local)
            USE_LOCAL=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -*)
            log_error "未知选项: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$CONFIG_FILE" ]]; then
                CONFIG_FILE="$1"
            else
                BUILD_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

# 启用调试模式
if [[ "$DEBUG" == "true" ]]; then
    set -x
    log_info "调试模式已启用"
fi

# 清理函数
cleanup() {
    if [[ "$CLEAN" == "true" ]]; then
        log_info "清理 Docker 容器和镜像..."
        docker container rm -f "$CONTAINER_NAME" 2>/dev/null || true
        docker image rm -f "$IMAGE_NAME:$IMAGE_TAG" 2>/dev/null || true
        log_success "清理完成"
        exit 0
    fi
}

# 检查本地 conda 环境
check_local_conda() {
    if ! command -v conda &> /dev/null; then
        log_error "conda 未找到。请安装 Miniconda 或 Anaconda"
        log_info "安装指南: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi

    # 检查 ubuntu-fai 环境是否存在
    if ! conda env list | grep -q "ubuntu-fai"; then
        log_error "conda 环境 'ubuntu-fai' 未找到"
        log_info "请运行: ./setup-conda-env.sh"
        exit 1
    fi

    log_info "使用本地 conda 环境: ubuntu-fai"
}

# 检查 Docker 可用性（仅非本地模式）
check_docker() {
    if [[ "$USE_LOCAL" == "true" ]]; then
        return 0
    fi

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或不在 PATH 中"
        log_info "请安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker 守护进程未运行"
        log_info "请启动 Docker 后重试"
        exit 1
    fi
}

# 构建 Docker 镜像
build_image() {
    local build_args=()
    
    if [[ "$NO_CACHE" == "true" ]]; then
        build_args+=("--no-cache")
    fi

    log_info "构建 Docker 镜像: $IMAGE_NAME:$IMAGE_TAG"
    
    if ! docker build "${build_args[@]}" -f "$DOCKERFILE" -t "$IMAGE_NAME:$IMAGE_TAG" "$SCRIPT_DIR"; then
        log_error "Docker 镜像构建失败"
        exit 1
    fi
    
    log_success "Docker 镜像构建成功"
}

# 检查并构建镜像
check_and_build_image() {
    if [[ "$USE_LOCAL" == "true" ]]; then
        return 0
    fi

    if [[ "$FORCE_BUILD" == "true" ]] || ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" &> /dev/null; then
        build_image
    else
        log_info "使用现有 Docker 镜像: $IMAGE_NAME:$IMAGE_TAG"
    fi
}

# 验证配置文件
validate_config() {
    if [[ -z "$CONFIG_FILE" ]]; then
        log_error "未指定配置文件"
        usage
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

    # 转换为绝对路径
    CONFIG_FILE="$(realpath "$CONFIG_FILE")"
    log_info "使用配置文件: $CONFIG_FILE"
}

# 准备输出目录
prepare_output_dir() {
    # 转换为绝对路径
    OUTPUT_DIR="$(realpath -m "$OUTPUT_DIR")"
    
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        log_info "创建输出目录: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
    
    if [[ ! -w "$OUTPUT_DIR" ]]; then
        log_error "输出目录不可写: $OUTPUT_DIR"
        exit 1
    fi
    
    log_info "使用输出目录: $OUTPUT_DIR"
}

# 获取用户信息（用于权限映射）
get_user_info() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        USER_ID=$(id -u)
        GROUP_ID=$(id -g)
    else
        # Linux
        USER_ID=$(id -u)
        GROUP_ID=$(id -g)
    fi
    
    log_info "运行容器使用 UID:GID = $USER_ID:$GROUP_ID"
}

# 本地模式运行
run_local() {
    log_info "使用本地 conda 环境运行构建..."
    
    # 激活 conda 环境并运行
    if conda run -n ubuntu-fai python build.py "$CONFIG_FILE" "${BUILD_ARGS[@]}"; then
        log_success "本地构建完成"
        log_info "检查输出目录: $OUTPUT_DIR"
    else
        log_error "本地构建失败"
        exit 1
    fi
}

# Docker 模式运行
run_container() {
    local docker_args=(
        "run"
        "--rm"
        "--name" "$CONTAINER_NAME"
        "--user" "$USER_ID:$GROUP_ID"
        "--volume" "$CONFIG_FILE:/app/config.json:ro"
        "--volume" "$OUTPUT_DIR:/app/output:rw"
        "--volume" "$SCRIPT_DIR:/app/host-src:ro"
        "--workdir" "/app"
    )

    # 添加特权模式用于 FAI 操作（ISO 创建需要 loop 设备）
    docker_args+=("--privileged")
    
    # 添加环境变量
    docker_args+=("--env" "PYTHONUNBUFFERED=1")
    
    if [[ "$DEBUG" == "true" ]]; then
        docker_args+=("--env" "FAI_DEBUG=1")
    fi

    # 添加镜像和命令
    docker_args+=("$IMAGE_NAME:$IMAGE_TAG")
    docker_args+=("python" "build.py" "config.json")
    docker_args+=("${BUILD_ARGS[@]}")

    log_info "启动 Ubuntu FAI 构建容器..."
    log_info "容器名称: $CONTAINER_NAME"
    log_info "配置文件: $CONFIG_FILE"
    log_info "输出目录: $OUTPUT_DIR"
    
    if ! docker "${docker_args[@]}"; then
        log_error "容器执行失败"
        exit 1
    fi
    
    log_success "构建完成"
    log_info "检查输出目录: $OUTPUT_DIR"
}

# 主执行函数
main() {
    # 处理清理请求
    cleanup
    
    # 验证环境
    if [[ "$USE_LOCAL" == "true" ]]; then
        check_local_conda
    else
        check_docker
    fi
    
    # 验证输入
    validate_config
    prepare_output_dir
    
    # 执行构建
    if [[ "$USE_LOCAL" == "true" ]]; then
        run_local
    else
        get_user_info
        check_and_build_image
        run_container
    fi
}

# 信号处理
trap 'log_warning "用户中断"; exit 130' INT TERM

# 运行主函数
main "$@"