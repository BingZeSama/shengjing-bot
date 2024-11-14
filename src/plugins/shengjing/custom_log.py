from nonebot.log import logger
from loguru import logger as loguru_logger
import sys
import re

from src.plugins.shengjing.config import GROUP_WHITELIST


def console_filter(record):
    # Match `group_id` like `123456789` in
    # `Message -456456456 from 123123123@[群:123456789] 'Ciallo～(∠・ω< )⌒☆'`
    pattern = r"(?<=@\[群:)\d+(?=\] ')"
    message = record["message"]
    match = re.search(pattern, message)

    try:
        first_match = match.group(1)
    except (IndexError, AttributeError):
        first_match = ""

    # If the log contains `group_id`
    if first_match in GROUP_WHITELIST:
        return True

    return False


# Remove default handler
logger.remove()

# Filter console log output
logger.add(sys.stderr, filter=console_filter, colorize=True)

# Test logs
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.error("This is an error message")
logger.critical("This is a critical message")
