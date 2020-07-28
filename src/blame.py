import sublime
import sublime_plugin
import os
import subprocess

from .common import (
    SETTINGS_FILE_BASENAME,
    SETTINGS_KEY_COMMIT_SKIPPING_MODE,
    SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE,
)
from .util import view_is_suitable, communicate_error, platform_startupinfo
from .templates import blame_phantom_html_template, blame_phantom_css
from .commit_skipping import BlameSetCommitSkippingMode

# @todo #0 Add a [Prev] button to the phantom, that causes it to reflect the previous commit that changed the line.
#  This has some overlap with the "commit-skipping" feature and possibly obsoletes it?


class Blame(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, "git-blame")

    def run(self, edit):
        if not view_is_suitable(self.view):
            return

        phantoms = []
        self.view.erase_phantoms("git-blame")
        # Before adding the phantom, see if the current phantom that is displayed is at the same spot at the selection
        if self.phantom_set.phantoms:
            phantom_exists = self.view.line(self.view.sel()[0]) == self.view.line(
                self.phantom_set.phantoms[0].region
            )
            if phantom_exists:
                self.phantom_set.update(phantoms)
                return

        for region in self.view.sel():
            line = self.view.line(region)
            (row, col) = self.view.rowcol(region.begin())
            full_path = self.view.file_name()

            try:
                blame_output = self.get_blame(int(row) + 1, full_path)
            except Exception as e:
                communicate_error(e)
                return

            sha, user, date, time = self.parse_blame(blame_output)

            phantom = sublime.Phantom(
                line,
                blame_phantom_html_template.format(
                    css=blame_phantom_css, sha=sha, user=user, date=date, time=time
                ),
                sublime.LAYOUT_BLOCK,
                self.on_phantom_close,
            )
            phantoms.append(phantom)
        self.phantom_set.update(phantoms)

    def on_phantom_close(self, href):
        href_parts = href.split("-")

        if len(href_parts) > 1:
            intent = href_parts[0]
            sha = href_parts[1]
            # The SHA output by git-blame may have a leading caret to indicate
            # that it is a "boundary commit". That useful information has
            # already been shown in the phantom, so strip it before going on to
            # use the SHA programmatically.
            sha = sha.strip("^")

            if intent == "copy":
                sublime.set_clipboard(sha)
                sublime.status_message("Git SHA copied to clipboard")
            elif intent == "show":
                try:
                    desc = self.get_commit(sha, self.view.file_name())
                except Exception as e:
                    communicate_error(e)
                    return

                buf = self.view.window().new_file()
                buf.run_command(
                    "blame_insert_commit_description",
                    {"desc": desc, "scratch_view_name": "commit " + sha},
                )
            else:
                self.view.erase_phantoms("git-blame")
        else:
            self.view.erase_phantoms("git-blame")

    # ------------------------------------------------------------

    def get_blame(self, line, path):
        cmd_line = [
            "git",
            "blame",
            "--minimal",
            "-w",
            "-L {0},{0}".format(line),
            os.path.basename(path),
        ]

        # @todo #21 Factor out loading of the commit-skipping mode so that the BlameShowAll command can use it too.
        skipping_mode = self.view.settings().get(
            SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE, None
        )
        if skipping_mode is None:
            settings_file = sublime.load_settings(SETTINGS_FILE_BASENAME)
            skipping_mode = settings_file.get(
                SETTINGS_KEY_COMMIT_SKIPPING_MODE, BlameSetCommitSkippingMode.MODE_NONE
            )
        try:
            cmd_line += BlameSetCommitSkippingMode.DETAIL[skipping_mode]["git_args"]
        except KeyError as e:
            communicate_error("Unexpected commit skipping mode: {0}".format(e))

        # print(cmd_line)
        return subprocess.check_output(
            cmd_line,
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

    def parse_blame(self, blame):
        sha, file_path, user, date, time, tz_offset, *_ = blame.split()

        # Was part of the inital commit so no updates
        if file_path[0] == "(":
            user, date, time, tz_offset = file_path, user, date, time
            file_path = None

        # Fix an issue where the username has a space
        # Im going to need to do something better though if people
        # start to have multiple spaces in their names.
        if not date[0].isdigit():
            user = "{0} {1}".format(user, date)
            date, time = time, tz_offset

        return (sha, user[1:], date, time)

    def get_commit(self, sha, path):
        return subprocess.check_output(
            ["git", "show", "--no-color", sha],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")


class BlameInsertCommitDescription(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.assign_syntax("Packages/Diff/Diff.sublime-syntax")
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)
