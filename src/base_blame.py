import os
import subprocess
from abc import ABCMeta, abstractmethod

from .settings import PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, pkg_settings
from .util import platform_startupinfo


class BaseBlame(metaclass=ABCMeta):
    def get_blame(self, path, **kwargs):
        # The option --show-name is necessary to force file name display even when this file has never been renamed.
        cmd_line = ["git", "blame", "--show-name", "--minimal", "-w"]
        cmd_line.extend(self.extra_cli_args(**kwargs))
        cmd_line.extend(pkg_settings().get(PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, []))
        cmd_line.extend(["--", os.path.basename(path)])
        # print(cmd_line)
        return subprocess.check_output(
            cmd_line,
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    def get_commit(self, sha, path):
        return subprocess.check_output(
            ["git", "show", "--no-color", sha],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    # ------------------------------------------------------------

    @abstractmethod
    def extra_cli_args(self, **kwargs):
        ...
