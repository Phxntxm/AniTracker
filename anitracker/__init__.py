import sys
import typing

__version__ = "1.3.6"
user_agent = f"AniTracker/{__version__} (Language=py)"
frozen_path: typing.Optional[str] = getattr(sys, "_MEIPASS", None)

ffprobe_cmd = "ffprobe"
ffmpeg_cmd = "ffmpeg"

if frozen_path is not None:
    if sys.platform.startswith("win32"):
        ffprobe_cmd = f"{frozen_path}\\ffprobe.exe"
        ffmpeg_cmd = f"{frozen_path}\\ffmpeg.exe"
    elif sys.platform.startswith("linux"):
        ffprobe_cmd = f"{frozen_path}/ffprobe"
        ffmpeg_cmd = f"{frozen_path}/ffmpeg"


def setup_logger():

    import logging
    import os

    # I may move to onedir and not onefile pyinstaller option, so handle this
    # if we are a directory, then just log there regardless
    if frozen_path == os.path.dirname(sys.executable):
        path = f"{frozen_path}/anitracker.log"
    # We know we're in onefile mode now
    elif sys.platform.startswith("linux"):
        # Weird there's no real standard for user logs
        path = os.path.expanduser("~/anitracker.log")
    elif sys.platform.startswith("win32"):
        path = os.path.expanduser(f"{os.path.dirname(sys.executable)}/anitracker.log")
    else:
        # For now just default to the same directory as the executable
        path = os.path.expanduser(f"{os.path.dirname(sys.executable)}/anitracker.log")

    logger = logging.getLogger("anitracker")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.FileHandler(path))

    return logger


logger = setup_logger()
# Don't want this in the namespace
del setup_logger
del sys
del typing

from .config import Config
from .anitracker import AniTracker
