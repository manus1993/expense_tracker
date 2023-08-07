import logging
import logging.handlers
import os
import sys

# from datetime import datetime
# from .splunk_logger import SplunkLoggingHandler

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", logging.INFO)
# today = datetime.now()
# today = "{}-{}-{}".format(str(today.year), str(today.month), str(today.day))
fmt = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"  # noqa: E501
formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%dT%H:%M:%S ")
logger = logging.getLogger("IOS-Pedia-API")
# syslog = SplunkLoggingHandler
# logger.addHandler(syslog)

logging.basicConfig(
    stream=sys.stdout,
    level=LOGGING_LEVEL,
    format=fmt,
    datefmt="%d/%b/%Y %H:%M:%S",
    # filename="{}-ios-pedia-api.log".format(today),
    # filemode="a",
)

