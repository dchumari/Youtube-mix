import logging
import sys
from pathlib import Path

def setup_logger(name: str = "app", log_file: str = "logs/app.log", level=logging.INFO):
    """
    Sets up a logger that outputs to both console and file.
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger

    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(level)
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # File Handler
    f_handler = logging.FileHandler(log_file, encoding='utf-8')
    f_handler.setLevel(level)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

# Global instance for quick import
logger = setup_logger()
