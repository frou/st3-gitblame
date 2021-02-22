import os
import re
import subprocess
import sys
from abc import ABCMeta, abstractmethod

import sublime

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

    def get_blame_text(self, path, **kwargs):
        cli_args = ["blame", "--show-name", "--minimal", "-w"]
        cli_args.extend(self.extra_cli_args(**kwargs))
        cli_args.extend(pkg_settings().get(PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, []))
        cli_args.extend(["--", os.path.basename(path)])
        return self.run_git(path, cli_args)

    def get_commit_text(self, sha, path):
        cli_args = ["show", "--no-color", sha]
        return self.run_git(path, cli_args)

    @classmethod
    def parse_line(cls, line):
        pattern = r"""(?x)
            ^   (?P<sha>\^?\w+)
            \s+ (?P<file>[\S ]+)
            \s+
            \(  (?P<author>.+?)
            \s+ (?P<date>\d{4}-\d{2}-\d{2})
            \s+ (?P<time>\d{2}:\d{2}:\d{2})
            \s+ (?P<timezone>[\+-]\d+)
            \s+ (?P<line_number>\d+)
            \)
            \s
            """
        # re's module-level functions like match(...) internally cache the compiled form of pattern strings.
        m = re.match(pattern, line)
        return m.groupdict() if m else {}

    def has_suitable_view(self):
        return (
            hasattr(self, "view") and self.view.file_name() and not self.view.is_dirty()  # type: ignore[attr-defined]
        )

    def tell_user_to_save(self):
        self.communicate_error("Please save file changes to disk first.")

    def communicate_error(self, e, modal=True):
        user_msg = "Git blame:\n\n{0}".format(e)
        if isinstance(e, subprocess.CalledProcessError):
            user_msg += "\n\n{0}".format(e.output.decode("utf-8"))

        print()  # noqa: T001
        if modal:
            sublime.error_message(user_msg)
        else:
            sublime.status_message(user_msg)
            # Unlike with the error dialog, a status message is not automatically
            # persisted in the console too.
            print(user_msg)  # noqa: T001

    # ------------------------------------------------------------

    @abstractmethod
    def extra_cli_args(self, **kwargs):
        ...
