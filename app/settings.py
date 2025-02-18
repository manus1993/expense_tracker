import os
import pathlib

from starlette.config import Config

config = Config()

if os.getenv("ENVIRONMENT") == "shared":
    root_path = "/api"
elif os.getenv("ENVIRONMENT") == "shared-dev":
    root_path = "/api"
else:
    root_path = ""


SCRIPT_NAME = config("SCRIPT_NAME", default=root_path)
path = pathlib.Path(__file__).parent.absolute()

with open(f"{path}/version.txt") as f:
    VERSION = f.read().strip()
