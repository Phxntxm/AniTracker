__version__ = "1.1.2"
user_agent = f"AniTracker/{__version__} (Language=py)"

def setup_logger():

    import logging
    import os
    import sys

    # I may move to onedir and not onefile pyinstaller option, so handle this
    # if we are a directory, then just log there regardless
    if hasattr(sys, "_MEIPASS") and sys._MEIPASS == os.path.dirname(sys.executable):
        path = f"{sys._MEIPASS}/anitracker.log"
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

from .config import Config
from .anitracker import AniTracker