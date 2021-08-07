from __future__ import annotations

import subprocess
from typing import List, Optional, Tuple, Union, TYPE_CHECKING
from anitracker import logger

if TYPE_CHECKING:
    from subprocess import IO

path: str = logger.handlers[0].baseFilename  # type: ignore


def run(
    cmd: List[str],
    *,
    stdout: Optional[Union[IO, int]] = None,
    stderr: Optional[Union[IO, int]] = None,
    stdin: Optional[Union[IO, int]] = None,
    **kwargs
) -> Tuple[Optional[str], Optional[str]]:
    with open(path, "a+") as f:
        if stdout is None:
            stdout = f
        if stderr is None:
            stderr = f
        if stdin is None:
            stdin = subprocess.DEVNULL

        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, stdin=stdin, **kwargs)
        out, err = p.communicate()

        if isinstance(out, bytes):
            out = out.decode()
        if isinstance(err, bytes):
            err = err.decode()

        return out, err


def Popen(
    cmd: List[str],
    *,
    stdout: Optional[Union[IO, int]] = None,
    stderr: Optional[Union[IO, int]] = None,
    stdin: Optional[Union[IO, int]] = None,
    **kwargs
) -> subprocess.Popen[str]:
    with open(path, "a+") as f:
        if stdout is None:
            stdout = f
        if stderr is None:
            stderr = f
        if stdin is None:
            stdin = subprocess.DEVNULL

        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, stdin=stdin, **kwargs)
        return p
