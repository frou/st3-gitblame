import sublime
import sublime_plugin

import os
import re
import subprocess

from .util import view_is_suitable, communicate_error, platform_startupinfo
from .templates import blame_all_phantom_html_template, blame_all_phantom_css

PHANTOM_KEY_ALL = "git-blame-all"
SETTING_PHANTOM_ALL_DISPLAYED = "git-blame-all-displayed"


class BlameShowAll(sublime_plugin.TextCommand):

    # The fixed length for author names
    NAME_LENGTH = 10

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY_ALL)
        self.pattern = None

    def run(self, edit):
        if not view_is_suitable(self.view):
            return

        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        phantoms = []

        # If they are currently shown, toggle them off and return.
        if self.view.settings().get(SETTING_PHANTOM_ALL_DISPLAYED, False):
            self.phantom_set.update(phantoms)
            self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, False)
            return

        try:
            blame_output = self.get_blame(self.view.file_name())
        except Exception as e:
            communicate_error(e)
            return

        for l in blame_output.splitlines():
            parsed = self.parse_blame(l)
            if not parsed:
                continue

            sha, author, date, time, line_number = parsed

            line_point = self.get_line_point(line_number - 1)
            phantom = sublime.Phantom(
                line_point,
                blame_all_phantom_html_template.format(
                    css=blame_all_phantom_css,
                    sha=sha,
                    user=self.format_name(author),
                    date=date,
                    time=time,
                ),
                sublime.LAYOUT_INLINE,
                self.on_phantom_close,
            )
            phantoms.append(phantom)

        self.phantom_set.update(phantoms)
        self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, True)
        # Bring the phantoms into view without the user needing to manually scroll left.
        self.view.set_viewport_position((0.0, self.view.viewport_position()[1]))

    def get_blame(self, path):
        return subprocess.check_output(
            # The option --show-name is necessary to force file name display.
            ["git", "blame", "--show-name", "--minimal", "-w", os.path.basename(path)],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    def parse_blame(self, blame):
        """Parses git blame output.
        """
        if not self.pattern:
            self.prepare_pattern()

        m = self.pattern.match(blame)
        if m:
            sha = m.group("sha")
            # Currently file is not used.
            # file = m.group('file')
            author = m.group("author")
            date = m.group("date")
            time = m.group("time")
            line_number = int(m.group("line_number"))
            return sha, author, date, time, line_number
        else:
            return None

    def prepare_pattern(self):
        """Prepares the regex pattern to parse git blame output.
        """
        # The SHA output by git-blame may have a leading caret to indicate
        # that it is a "boundary commit".
        p_sha = r"(?P<sha>\^?\w+)"
        p_file = r"((?P<file>[\S ]+)\s+)"
        p_author = r"(?P<author>.+?)"
        p_date = r"(?P<date>\d{4}-\d{2}-\d{2})"
        p_time = r"(?P<time>\d{2}:\d{2}:\d{2})"
        p_timezone = r"(?P<timezone>[\+-]\d+)"
        p_line = r"(?P<line_number>\d+)"
        s = r"\s+"

        self.pattern = re.compile(
            r"^"
            + p_sha
            + s
            + p_file
            + r"\("
            + p_author
            + s
            + p_date
            + s
            + p_time
            + s
            + p_timezone
            + s
            + p_line
            + r"\) "
        )

    def format_name(self, name):
        """Formats author names so that widths of phantoms become equal.
        """
        ellipsis = "..."
        if len(name) > self.NAME_LENGTH:
            return name[: self.NAME_LENGTH] + ellipsis
        else:
            return name + "." * (self.NAME_LENGTH - len(name)) + ellipsis

    def get_line_point(self, line):
        """Get the point of specified line in a view.
        """
        return self.view.line(self.view.text_point(line, 0))

    def on_phantom_close(self, href):
        """Closes opened phantoms.
        """
        if href == "close":
            self.view.run_command("blame_erase_all")


class BlameEraseAll(sublime_plugin.TextCommand):
    def run(self, edit):
        """Erases the blame results.
        """
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)


class BlameEraseAllListener(sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        """Checks if the blame_erase_all command is applicable.
        """
        return settings.get(SETTING_PHANTOM_ALL_DISPLAYED, False)

    def on_modified_async(self):
        """Automatically erases the blame results to prevent mismatches.
        """
        self.view.run_command("blame_erase_all")
        self.view.settings().erase(SETTING_PHANTOM_ALL_DISPLAYED)
