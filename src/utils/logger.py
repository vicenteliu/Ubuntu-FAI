"""增强的日志系统 - Ubuntu FAI Build System"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 自定义格式
        record.colored_levelname = f"{color}{record.levelname}{reset}"
        record.colored_name = f"\033[94m{record.name}{reset}"  # 蓝色
        
        return super().format(record)


class JSONLogFormatter(logging.Formatter):
    """JSON 格式的日志格式化器（用于机器可读的日志）"""
    
    def format(self, record):
        """格式化为 JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加额外的字段
        if hasattr(record, 'build_phase'):
            log_data['build_phase'] = record.build_phase
        if hasattr(record, 'config_file'):
            log_data['config_file'] = record.config_file
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
            
        return json.dumps(log_data, ensure_ascii=False)


class BuildLogger:
    """Ubuntu FAI 构建系统的增强日志管理器"""
    
    def __init__(self, 
                 name: str = "ubuntu-fai",
                 log_dir: Path = None,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True,
                 debug: bool = False):
        """初始化日志系统
        
        Args:
            name: 日志器名称
            log_dir: 日志目录路径
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件日志
            enable_json: 是否启用 JSON 格式日志
            debug: 是否启用调试模式
        """
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.debug = debug
        
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置主日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 设置不同类型的处理器
        if enable_console:
            self._setup_console_handler()
        
        if enable_file:
            self._setup_file_handler()
            
        if enable_json:
            self._setup_json_handler()
    
    def _setup_console_handler(self):
        """设置控制台日志处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        # 彩色格式
        console_format = "%(colored_levelname)s %(colored_name)s - %(message)s"
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """设置文件日志处理器"""
        # 主日志文件
        log_file = self.log_dir / "build.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 详细格式
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
        
        # 错误日志文件（只记录错误和警告）
        error_file = self.log_dir / "error.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(error_handler)
    
    def _setup_json_handler(self):
        """设置 JSON 格式日志处理器"""
        json_file = self.log_dir / "build.json"
        json_handler = logging.FileHandler(json_file, encoding='utf-8')
        json_handler.setLevel(logging.DEBUG)
        
        json_formatter = JSONLogFormatter()
        json_handler.setFormatter(json_formatter)
        
        self.logger.addHandler(json_handler)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """获取日志器
        
        Args:
            name: 子日志器名称
            
        Returns:
            配置好的日志器
        """
        if name:
            return logging.getLogger(f"{self.name}.{name}")
        return self.logger
    
    def log_build_start(self, config_file: str, **kwargs):
        """记录构建开始"""
        logger = self.get_logger("build")
        extra = {'build_phase': 'start', 'config_file': config_file}
        extra.update(kwargs)
        
        logger.info(f"开始构建进程 - 配置文件: {config_file}", extra=extra)
    
    def log_build_end(self, success: bool, duration: float, **kwargs):
        """记录构建结束"""
        logger = self.get_logger("build")
        extra = {'build_phase': 'end', 'duration': duration}
        extra.update(kwargs)
        
        if success:
            logger.info(f"构建成功完成 - 耗时: {duration:.2f}s", extra=extra)
        else:
            logger.error(f"构建失败 - 耗时: {duration:.2f}s", extra=extra)
    
    def log_phase_start(self, phase: str, **kwargs):
        """记录构建阶段开始"""
        logger = self.get_logger("build")
        extra = {'build_phase': phase}
        extra.update(kwargs)
        
        logger.info(f"开始阶段: {phase}", extra=extra)
    
    def log_phase_end(self, phase: str, success: bool, duration: float = None, **kwargs):
        """记录构建阶段结束"""
        logger = self.get_logger("build")
        extra = {'build_phase': phase}
        if duration:
            extra['duration'] = duration
        extra.update(kwargs)
        
        status = "完成" if success else "失败"
        message = f"阶段 {phase} {status}"
        if duration:
            message += f" - 耗时: {duration:.2f}s"
            
        if success:
            logger.info(message, extra=extra)
        else:
            logger.error(message, extra=extra)
    
    def log_config_validation(self, config_file: str, is_valid: bool, errors: list = None, warnings: list = None):
        """记录配置验证结果"""
        logger = self.get_logger("config")
        extra = {'build_phase': 'validation', 'config_file': config_file}
        
        if is_valid:
            logger.info(f"配置验证通过: {config_file}", extra=extra)
            if warnings:
                for warning in warnings:
                    logger.warning(f"配置警告: {warning}", extra=extra)
        else:
            logger.error(f"配置验证失败: {config_file}", extra=extra)
            if errors:
                for error in errors:
                    logger.error(f"配置错误: {error}", extra=extra)
    
    def log_download_progress(self, item: str, progress: float, total_size: int = None):
        """记录下载进度"""
        logger = self.get_logger("download")
        extra = {'build_phase': 'download', 'progress': progress}
        if total_size:
            extra['total_size'] = total_size
        
        message = f"下载进度 {item}: {progress:.1f}%"
        if total_size:
            message += f" ({total_size} bytes)"
            
        logger.debug(message, extra=extra)
    
    def log_template_generation(self, template_name: str, output_file: str, success: bool):
        """记录模板生成结果"""
        logger = self.get_logger("template")
        extra = {'build_phase': 'template', 'template': template_name, 'output': output_file}
        
        if success:
            logger.info(f"模板生成成功: {template_name} -> {output_file}", extra=extra)
        else:
            logger.error(f"模板生成失败: {template_name}", extra=extra)
    
    def create_session_summary(self, session_id: str = None) -> dict:
        """创建会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要信息
        """
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        summary = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'log_files': {
                'main': str(self.log_dir / "build.log"),
                'error': str(self.log_dir / "error.log"),
                'json': str(self.log_dir / "build.json")
            }
        }
        
        # 保存摘要
        summary_file = self.log_dir / f"session_{session_id}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary


def setup_logging(debug: bool = False, 
                 log_dir: str = "logs",
                 enable_json: bool = True) -> BuildLogger:
    """设置 Ubuntu FAI 构建系统的日志
    
    Args:
        debug: 是否启用调试模式
        log_dir: 日志目录
        enable_json: 是否启用 JSON 日志
        
    Returns:
        配置好的 BuildLogger 实例
    """
    return BuildLogger(
        name="ubuntu-fai",
        log_dir=Path(log_dir),
        debug=debug,
        enable_json=enable_json
    )


# 创建默认日志器实例
default_logger = None

def get_logger(name: str = None) -> logging.Logger:
    """获取默认日志器
    
    Args:
        name: 子日志器名称
        
    Returns:
        日志器实例
    """
    global default_logger
    if default_logger is None:
        default_logger = setup_logging()
    
    return default_logger.get_logger(name)