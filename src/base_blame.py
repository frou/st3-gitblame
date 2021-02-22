import os
import subprocess
import sys
from abc import ABCMeta, abstractmethod

from .settings import PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, pkg_settings


class BaseBlame(metaclass=ABCMeta):
    def run_git(self, view_file_path, cli_args):
        if sys.platform == "win32":
            startup_info = subprocess.STARTUPINFO()
            # Stop a visible console window from appearing.
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = subprocess.SW_HIDE
        else:
            startup_info = None

        cmd_line = ["git"] + cli_args
        # print(cmd_line)

        return subprocess.check_output(
            cmd_line,
            cwd=os.path.dirname(os.path.realpath(view_file_path)),
            startupinfo=startup_info,
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    def get_blame(self, path, **kwargs):
        cli_args = ["blame", "--show-name", "--minimal", "-w"]
        cli_args.extend(self.extra_cli_args(**kwargs))
        cli_args.extend(pkg_settings().get(PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, []))
        cli_args.extend(["--", os.path.basename(path)])
        return self.run_git(path, cli_args)

    def get_commit(self, sha, path):
        cli_args = ["show", "--no-color", sha]
        return self.run_git(path, cli_args)

    # ------------------------------------------------------------

    @abstractmethod
    def extra_cli_args(self, **kwargs):
        ...
