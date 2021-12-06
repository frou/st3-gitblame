import os
import re
import subprocess
import sys
from abc import ABCMeta, abstractmethod
from urllib.parse import parse_qs, urlparse

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
        ).decode()

    def get_blame_text(self, path, **kwargs):
        cli_args = ["blame", "--show-name", "--minimal", "-w"]
        cli_args.extend(self.extra_cli_args(**kwargs))
        cli_args.extend(pkg_settings().get(PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, []))
        cli_args.extend(["--", os.path.basename(path)])
        return self.run_git(path, cli_args)

    def get_commit_fulltext(self, sha, path):
        cli_args = ["show", "--no-color", sha]
        return self.run_git(path, cli_args)

    def get_commit_message_subject(self, sha, path):
        cli_args = ["show", "--no-color", sha, "--pretty=format:%s", "--no-patch"]
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

    # @todo Add a test for the `parse_line_with_relative_date` function in test_parsing.py
    @classmethod
    def parse_line_with_relative_date(cls, line):
        """
        The difference from parse_line is that date/time/timezone are replaced with relative_date
        to be able to parse human readable format
        https://github.com/git/git/blob/c09b6306c6ca275ed9d0348a8c8014b2ff723cfb/date.c#L131
        """
        pattern = r"""(?x)
            ^   (?P<sha>\^?\w+)
            \s+ (?P<file>[\S ]+)
            \s+
            \(  (?P<author>.+?)
            \s+ (?P<relative_date>\d+.+ago)
            \s+ (?P<line_number>\d+)
            \)
            \s
            """
        # re's module-level functions like match(...) internally cache the compiled form of pattern strings.
        m = re.match(pattern, line)
        return m.groupdict() if m else {}

    def handle_phantom_button(self, href):
        url = urlparse(href)
        querystring = parse_qs(url.query)
        # print(url)
        # print(querystring)

        if url.path == "copy":
            sublime.set_clipboard(querystring["sha"][0])
            sublime.status_message("Git SHA copied to clipboard")
        elif url.path == "show":
            sha = querystring["sha"][0]
            try:
                desc = self.get_commit_fulltext(sha, self._view().file_name())
            except Exception as e:
                self.communicate_error(e)
                return

            buf = self._view().window().new_file()
            buf.run_command(
                "blame_insert_commit_description",
                {"desc": desc, "scratch_view_name": "commit " + sha},
            )
        elif url.path == "prev":
            sha = querystring["sha"][0]
            row_num = querystring["row_num"][0]
            sha_skip_list = querystring.get("skip", [])
            if sha not in sha_skip_list:
                sha_skip_list.append(sha)
            self.rerun(
                prevving=True,
                fixed_row_num=int(row_num),
                sha_skip_list=sha_skip_list,
            )
        elif url.path == "close":
            self.close_by_user_request()
        else:
            self.communicate_error(
                "No handler for URL path '{0}' in phantom".format(url.path)
            )

    def has_suitable_view(self):
        view = self._view()
        return view.file_name() and not view.is_dirty()

    def tell_user_to_save(self):
        self.communicate_error("Please save file changes to disk first.")

    def communicate_error(self, e, modal=True):
        user_msg = "Git blame:\n\n{0}".format(e)
        if isinstance(e, subprocess.CalledProcessError):
            user_msg += "\n\n{0}".format(e.output.decode())

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
    def _view(self):
        ...

    @abstractmethod
    def close_by_user_request(self):
        ...

    @abstractmethod
    def extra_cli_args(self, **kwargs):
        ...

    @abstractmethod
    def rerun(self, **kwargs):
        ...
