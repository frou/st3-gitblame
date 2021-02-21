import os
import subprocess

import sublime
import sublime_plugin

from .parse import parse_blame_cli_output_line
from .settings import PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, pkg_settings
from .templates import blame_all_phantom_css, blame_all_phantom_html_template
from .util import communicate_error, platform_startupinfo, view_is_suitable

PHANTOM_KEY_ALL = "git-blame-all"
SETTING_PHANTOM_ALL_DISPLAYED = "git-blame-all-displayed"


class BlameShowAll(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY_ALL)
        self.pattern = None

    def run(self, edit):
        if not view_is_suitable(self.view):
            return

        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        phantoms = []  # type: list[sublime.Phantom]

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

        blames = [
            parse_blame_cli_output_line(line) for line in blame_output.splitlines()
        ]
        blames = [b for b in blames if b]
        if not blames:
            communicate_error(
                "Failed to parse anything for {0}. Has git's output format changed?".format(
                    self.__class__.__name__
                )
            )
            return

        max_author_len = max(len(b["author"]) for b in blames)
        for blame in blames:
            line_number = int(blame["line_number"])
            line_point = self.get_line_point(line_number - 1)

            author = blame["author"]

            phantom = sublime.Phantom(
                line_point,
                blame_all_phantom_html_template.format(
                    css=blame_all_phantom_css,
                    sha=blame["sha"],
                    user=author + "&nbsp;" * (max_author_len - len(author)),
                    date=blame["date"],
                    time=blame["time"],
                ),
                sublime.LAYOUT_INLINE,
                self.on_phantom_close,
            )
            phantoms.append(phantom)

        self.phantom_set.update(phantoms)
        self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, True)
        # Bring the phantoms into view without the user needing to manually scroll left.
        # @todo BlameAll: Automatically scrolling the view to the left doesn't work when the ST window has >1 Group
        self.view.set_viewport_position((0.0, self.view.viewport_position()[1]))

    def on_phantom_close(self, href):
        """Closes opened phantoms."""
        if href == "close":
            self.view.run_command("blame_erase_all")

    # ------------------------------------------------------------

    def get_blame(self, path):
        # The option --show-name is necessary to force file name display.
        cmd_line = ["git", "blame", "--show-name", "--minimal", "-w"]
        cmd_line.extend(pkg_settings().get(PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS, []))
        cmd_line.extend(["--", os.path.basename(path)])
        # print(cmd_line)
        return subprocess.check_output(
            cmd_line,
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    # @todo Consolidate the CLI parsing regex into a single string (use r"""(?x)""") and use it in Blame as well as BlameShowAll

    def get_line_point(self, line):
        """Get the point of specified line in a view."""
        return self.view.line(self.view.text_point(line, 0))


class BlameEraseAll(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def run(self, edit):
        """Erases the blame results."""
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)


class BlameEraseAllListener(sublime_plugin.ViewEventListener):

    # Overrides --------------------------------------------------

    @classmethod
    def is_applicable(cls, settings):
        """Checks if the blame_erase_all command is applicable."""
        return settings.get(SETTING_PHANTOM_ALL_DISPLAYED, False)

    def on_modified_async(self):
        """Automatically erases the blame results to prevent mismatches."""
        self.view.run_command("blame_erase_all")
        self.view.settings().erase(SETTING_PHANTOM_ALL_DISPLAYED)
