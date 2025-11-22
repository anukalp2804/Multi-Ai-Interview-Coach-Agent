# utils.py
import logging
from pathlib import Path

def setup_logging():
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "ai_interview.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ai-interview")

logger = setup_logging()
