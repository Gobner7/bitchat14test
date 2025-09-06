import logging
import sys
from datetime import datetime
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Create logs directory
LOG_DIR = Path("/workspace/csfloat_flipper/logs")
LOG_DIR.mkdir(exist_ok=True)

# Custom theme for rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "profit": "bold green",
    "loss": "bold red"
})

console = Console(theme=custom_theme)

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and symbols"""
    
    FORMATS = {
        logging.DEBUG: "🔍 %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.INFO: "ℹ️  %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.WARNING: "⚠️  %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.ERROR: "❌ %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.CRITICAL: "🚨 %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    
    def format(self, record):
        log_format = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
        return formatter.format(record)

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with Rich
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    console_handler.setLevel(logging.DEBUG)
    
    # File handler for all logs
    file_handler = logging.FileHandler(
        LOG_DIR / f"flipper_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Error file handler
    error_handler = logging.FileHandler(
        LOG_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
    ))
    
    # Trade log handler
    if 'trade' in name.lower() or 'sniper' in name.lower():
        trade_handler = logging.FileHandler(
            LOG_DIR / f"trades_{datetime.now().strftime('%Y%m%d')}.log"
        )
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        logger.addHandler(trade_handler)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger"""
    return setup_logger(name, level=config.log_level if 'config' in globals() else 'INFO')

# Performance logger for metrics
perf_logger = setup_logger('performance', 'DEBUG')

def log_trade(action: str, item: str, price: float, profit: float = None, **kwargs):
    """Log trade with formatting"""
    trade_logger = get_logger('trades')
    
    if action == 'BUY':
        trade_logger.info(f"🛒 BUY: {item} @ ${price:.2f}")
    elif action == 'SELL':
        if profit and profit > 0:
            trade_logger.info(f"💰 SELL: {item} @ ${price:.2f} | Profit: ${profit:.2f} ✅")
        elif profit and profit < 0:
            trade_logger.info(f"📉 SELL: {item} @ ${price:.2f} | Loss: ${abs(profit):.2f} ❌")
        else:
            trade_logger.info(f"💱 SELL: {item} @ ${price:.2f}")
    elif action == 'SNIPE':
        trade_logger.info(f"⚡ SNIPE: {item} @ ${price:.2f} | {kwargs.get('execution_time', 0):.1f}ms")
    
    # Log additional details
    if kwargs:
        trade_logger.debug(f"Details: {kwargs}")