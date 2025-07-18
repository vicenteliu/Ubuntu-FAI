# Ubuntu FAI Build System - 测试指南

🧪 **Ubuntu 24.04 原生环境测试完整指南**

本文档提供在 Ubuntu 24.04 主机上测试 Ubuntu FAI Build System 的详细说明和验证步骤。

## 📋 目录

- [测试环境要求](#测试环境要求)
- [环境准备](#环境准备)
- [基础功能测试](#基础功能测试)
- [详细功能测试](#详细功能测试)
- [错误场景测试](#错误场景测试)
- [性能测试](#性能测试)
- [高级测试场景](#高级测试场景)
- [测试检查清单](#测试检查清单)
- [故障排除](#故障排除)

## 🖥️ 测试环境要求

### 推荐系统配置
- **操作系统**: Ubuntu 24.04 LTS (x86_64 或 ARM64)
- **内存**: 最少 4GB RAM，推荐 8GB+
- **存储**: 最少 10GB 可用空间
- **网络**: 互联网连接（用于下载依赖和软件包）

### 必需软件
- Python 3.9+
- python3-venv (虚拟环境模块)
- python3-pip
- git

### 可选软件 (用于完整 ISO 构建)
- FAI tools (fai-server, fai-setup-storage)
- 虚拟化工具 (qemu-kvm, libvirt)

## 🚀 环境准备

### 1. 系统更新和依赖安装
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3 python3-venv python3-pip git curl wget

# 安装 FAI 工具 (可选)
sudo apt install -y fai-server fai-setup-storage

# 验证 Python 版本
python3 --version  # 应该 >= 3.9
```

### 2. 克隆项目
```bash
git clone <repository-url>
cd Ubuntu-FAI

# 检查项目文件完整性
ls -la
```

### 3. 设置虚拟环境
```bash
# 运行环境设置脚本
./setup-venv.sh

# 验证虚拟环境创建
ls -la ubuntu-fai-venv/
```

## 🧪 基础功能测试

### 测试 1: 虚拟环境验证
```bash
# 激活虚拟环境
source ubuntu-fai-venv/bin/activate

# 验证 Python 解释器
which python
python --version

# 验证关键依赖
python -c "import pydantic, jinja2, yaml, requests; print('所有依赖正常')"

# 退出虚拟环境
deactivate
```

**预期结果**:
- 虚拟环境成功激活
- Python 解释器指向虚拟环境
- 所有依赖包导入成功

### 测试 2: 配置验证测试
```bash
# 使用新脚本进行测试
./run.sh --help

# 基础配置验证
./run.sh --skip-downloads --skip-fai config.json.example
```

**预期结果**:
- 帮助信息正确显示
- 配置验证通过，无致命错误
- 生成 autoinstall 和 FAI 配置文件

### 测试 3: 日志系统验证
```bash
# 启用调试模式测试
./run.sh --debug --skip-downloads --skip-fai config.json.example

# 检查日志文件
ls -la logs/
cat logs/build.log
cat logs/build.json | head -5
```

**预期结果**:
- 控制台显示彩色调试输出
- 生成完整的日志文件
- JSON 日志格式正确

## 🔍 详细功能测试

### 测试 4: 配置文件生成验证
```bash
# 运行完整配置生成
./run.sh --skip-downloads --skip-fai config.json.example

# 验证输出文件
echo "=== Autoinstall 配置 ==="
head -20 output/user-data.yaml

echo "=== FAI 配置 ==="
ls -la output/fai-config/

echo "=== 首次启动配置 ==="
ls -la output/first-boot/
```

**预期结果**:
- 生成有效的 user-data.yaml 文件
- FAI 配置目录结构完整
- 首次启动脚本和服务文件存在

### 测试 5: 不同配置场景测试
```bash
# 创建自定义配置进行测试
cp config.json.example test-config.json

# 修改配置 (可选)
# 编辑 test-config.json 更改硬件类型、加密设置等

# 测试自定义配置
./run.sh --skip-downloads --skip-fai test-config.json

# 比较输出差异
diff output/user-data.yaml output.backup/user-data.yaml || echo "配置已更新"
```

**预期结果**:
- 不同配置生成不同的输出文件
- 配置变更反映在生成的文件中

### 测试 6: 模板渲染验证
```bash
# 检查模板文件
echo "=== 用户数据模板 ==="
grep -A 5 -B 5 "{% if" src/templates/user-data.yaml.j2

echo "=== 首次启动模板 ==="
grep -A 3 -B 3 "packages" src/templates/first-boot-script.sh.j2

# 验证模板语法
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('src/templates'))
templates = ['user-data.yaml.j2', 'first-boot.service.j2']
for t in templates:
    template = env.get_template(t)
    print(f'模板 {t} 语法正确')
"
```

**预期结果**:
- 模板文件包含正确的 Jinja2 语法
- 所有模板语法验证通过

## ❌ 错误场景测试

### 测试 7: 配置验证错误处理
```bash
# 创建无效配置文件
echo '{"invalid": "json"' > invalid-config.json

# 测试无效 JSON
./run.sh --skip-fai invalid-config.json 2>&1 | grep -i error

# 创建缺少必需字段的配置
echo '{"hardware": {"vendor": "dell"}}' > incomplete-config.json

# 测试不完整配置
./run.sh --skip-fai incomplete-config.json 2>&1 | grep -i error

# 清理测试文件
rm -f invalid-config.json incomplete-config.json
```

**预期结果**:
- 无效 JSON 被正确检测和报告
- 缺少必需字段的错误被捕获
- 错误信息清晰明了

### 测试 8: 网络错误处理
```bash
# 测试下载错误处理 (使用示例配置中的无效 URL)
./run.sh --skip-fai config.json.example 2>&1 | grep -A 5 -B 5 "404"

# 验证系统优雅处理下载失败
echo "检查日志中的错误处理..."
grep -i "download.*failed" logs/build.log || echo "未发现下载错误"
```

**预期结果**:
- 网络错误被正确捕获和报告
- 系统不会因下载失败而崩溃
- 错误日志提供有用的诊断信息

## ⚡ 性能测试

### 测试 9: 构建时间分析
```bash
# 运行性能测试
echo "开始性能测试..."
time ./run.sh --skip-downloads --skip-fai config.json.example

# 分析阶段耗时
echo "=== 构建阶段耗时分析 ==="
grep "阶段.*完成.*耗时" logs/build.log

# 检查日志文件大小
echo "=== 日志文件大小 ==="
ls -lh logs/
```

**预期结果**:
- 完整构建在合理时间内完成 (< 30 秒用于配置生成)
- 各阶段耗时记录清晰
- 日志文件大小合理 (< 1MB)

### 测试 10: 内存使用监控
```bash
# 监控内存使用
echo "监控构建过程内存使用..."

# 后台运行构建
./run.sh --skip-downloads --skip-fai config.json.example &
BUILD_PID=$!

# 监控内存使用
while kill -0 $BUILD_PID 2>/dev/null; do
    ps -o pid,vsz,rss,comm -p $BUILD_PID
    sleep 1
done

echo "构建完成，内存监控结束"
```

**预期结果**:
- 内存使用稳定，无明显内存泄漏
- 峰值内存使用 < 500MB

## 🚀 高级测试场景

### 测试 11: 并发安全测试
```bash
# 创建多个配置文件
cp config.json.example config-test1.json
cp config.json.example config-test2.json
cp config.json.example config-test3.json

# 并发运行多个构建
echo "开始并发测试..."
./run.sh --skip-downloads --skip-fai config-test1.json &
./run.sh --skip-downloads --skip-fai config-test2.json &
./run.sh --skip-downloads --skip-fai config-test3.json &

# 等待所有任务完成
wait

echo "并发测试完成"
rm -f config-test*.json
```

**预期结果**:
- 所有并发构建成功完成
- 无文件冲突或竞争条件
- 日志文件正确分离

## ✅ 测试检查清单

### 基础功能检查
- [ ] 虚拟环境正确创建和激活
- [ ] 所有 Python 依赖正确安装
- [ ] 配置文件验证正常工作
- [ ] 帮助信息正确显示

### 配置生成检查
- [ ] Autoinstall 配置 (user-data.yaml) 生成正确
- [ ] FAI 配置文件结构完整
- [ ] 首次启动脚本生成正确
- [ ] 模板渲染无语法错误

### 日志系统检查
- [ ] 控制台输出彩色格式正确
- [ ] 文件日志格式标准
- [ ] JSON 日志结构正确
- [ ] 构建阶段计时准确

### 错误处理检查
- [ ] 无效配置被正确拒绝
- [ ] 网络错误优雅处理
- [ ] 文件权限错误正确报告
- [ ] 错误信息清晰有用

### 性能检查
- [ ] 构建时间在合理范围内
- [ ] 内存使用稳定
- [ ] 临时文件正确清理
- [ ] 并发执行无冲突

## 🔧 故障排除

### 常见问题及解决方法

#### 1. 虚拟环境创建失败
```bash
# 检查 Python 版本
python3 --version

# 安装 venv 模块
sudo apt install python3-venv

# 删除并重新创建
rm -rf ubuntu-fai-venv
./setup-venv.sh
```

#### 2. 依赖安装失败
```bash
# 激活虚拟环境
source ubuntu-fai-venv/bin/activate

# 升级 pip
python -m pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt
```

#### 3. 配置验证错误
```bash
# 检查配置文件语法
python -m json.tool config.json.example

# 手动运行配置验证
python -c "
from src.config.models import BuildConfig
try:
    config = BuildConfig.from_file('config.json.example')
    print('配置验证通过')
except Exception as e:
    print(f'配置错误: {e}')
"
```

#### 4. 权限问题
```bash
# 检查文件权限
ls -la setup-venv.sh run.sh

# 修复执行权限
chmod +x setup-venv.sh run.sh activate-venv.sh

# 检查输出目录权限
ls -la output/
```

#### 5. 日志分析
```bash
# 查看最新日志
tail -f logs/build.log

# 搜索错误信息
grep -i error logs/build.log

# 查看 JSON 日志
jq '.level, .message' logs/build.json | tail -20
```

## 📊 测试报告模板

```
# Ubuntu FAI Build System 测试报告

## 测试环境
- 操作系统: Ubuntu 24.04 LTS
- Python 版本: 3.x.x
- 测试日期: YYYY-MM-DD
- 测试人员: [姓名]

## 测试结果汇总
- 总测试项目: 11
- 通过项目: X
- 失败项目: X
- 跳过项目: X

## 详细结果
[详细记录每个测试的结果]

## 发现的问题
[记录任何问题和建议的解决方案]

## 建议
[改进建议和后续行动项]
```

---

🎯 **测试目标**: 确保 Ubuntu FAI Build System 在 Ubuntu 24.04 环境中稳定可靠地运行，所有核心功能正常工作。