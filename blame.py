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
from .commit_skipping import BlameSetCommitSkippingMode

# @todo #0 Move the HTML/CSS templates to a separate source file.

stylesheet_one = """
    <style>
        div.phantom-arrow {
            border-top: 0.4rem solid transparent;
            border-left: 0.5rem solid color(var(--bluish) blend(var(--background) 30%));
            width: 0;
            height: 0;
        }
        div.phantom {
            padding: 0.4rem 0 0.4rem 0.7rem;
            margin: 0 0 0.2rem;
            border-radius: 0 0.2rem 0.2rem 0.2rem;
            background-color: color(var(--bluish) blend(var(--background) 30%));
        }
        div.phantom span.message {
            padding-right: 0.7rem;
        }
        div.phantom a {
            text-decoration: inherit;
        }
        div.phantom a.close {
            padding: 0.35rem 0.7rem 0.45rem 0.8rem;
            position: relative;
            bottom: 0.05rem;
            border-radius: 0 0.2rem 0.2rem 0;
            font-weight: bold;
        }
        html.dark div.phantom a.close {
            background-color: #00000018;
        }
        html.light div.phantom a.close {
            background-color: #ffffff18;
        }
    </style>
"""

template_one = """
    <body id="inline-git-blame">
        {stylesheet}
        <div class="phantom-arrow"></div>
        <div class="phantom">
            <span class="message">
                <strong>Git Blame</strong> ({user})
                {date} {time} |
                {sha}
                <a href="copy-{sha}">[Copy]</a>
                <a href="show-{sha}">[Show]</a>
                <a class="close" href="close">\u00D7</a>
            </span>
        </div>
    </body>
"""


class BlameCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view
        self.phantom_set = sublime.PhantomSet(view, "git-blame")

    def get_blame(self, line, path):
        cmd_line = [
            "git",
            "blame",
            "--minimal",
            "-w",
            "-L {0},{0}".format(line),
            os.path.basename(path),
        ]

        # @todo #21 Factor out loading of the commit-skipping mode so that BlameShowAllCommand can use it too.
        skipping_mode = self.view.settings().get(
            SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE, None
        )
        if skipping_mode is None:
            settings_file = sublime.load_settings(SETTINGS_FILE_BASENAME)
            skipping_mode = settings_file.get(
                SETTINGS_KEY_COMMIT_SKIPPING_MODE, BlameSetCommitSkippingMode.MODE_NONE
            )
        try:
            cmd_line += BlameSetCommitSkippingMode.METADATA[skipping_mode]["git_args"]
        except KeyError as e:
            communicate_error("Unexpected commit skipping mode: {0}".format(e))
        # sublime.message_dialog(str(cmd_line))

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
            ["git", "show", sha],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=platform_startupinfo(),
            stderr=subprocess.STDOUT,
        ).decode("utf-8")

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
                    "insert_commit_description",
                    {"desc": desc, "scratch_view_name": "commit " + sha},
                )
            else:
                self.view.erase_phantoms("git-blame")
        else:
            self.view.erase_phantoms("git-blame")

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

            body = template_one.format(
                sha=sha, user=user, date=date, time=time, stylesheet=stylesheet_one
            )

            phantom = sublime.Phantom(
                line, body, sublime.LAYOUT_BLOCK, self.on_phantom_close
            )
            phantoms.append(phantom)
        self.phantom_set.update(phantoms)


class InsertCommitDescriptionCommand(sublime_plugin.TextCommand):
    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.set_syntax_file("Packages/Diff/Diff.sublime-syntax")
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)
