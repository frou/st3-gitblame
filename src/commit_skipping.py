from collections import namedtuple

import sublime
import sublime_plugin

from .common import (
    SETTINGS_FILE_BASENAME,
    SETTINGS_KEY_COMMIT_SKIPPING_MODE,
    SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE,
)


class BlameSetCommitSkippingMode(sublime_plugin.TextCommand):
    MODE_NONE = False
    MODE_SAME_FILE_SAME_COMMIT = "same_file_same_commit"
    MODE_CROSS_FILE_SAME_COMMIT = "cross_file_same_commit"
    MODE_CROSS_ANY_FILE = "cross_any_file"
    MODE_CROSS_ANY_HISTORICAL_FILE = "cross_any_historical_file"

    ModeMetadata = namedtuple("ModeMetadata", ["elaboration", "git_args"])

    DETAIL = {
        MODE_NONE: ModeMetadata("<NONE>", []),
        MODE_SAME_FILE_SAME_COMMIT: ModeMetadata(
            "...moved/copied the line within a file", ["-M"]
        ),
        MODE_CROSS_FILE_SAME_COMMIT: ModeMetadata(
            "...moved/copied the line from another file modified in the same commit",
            ["-C"],
        ),
        MODE_CROSS_ANY_FILE: ModeMetadata(
            "...created the file with a copy of a line from any other file", ["-C"] * 2
        ),
        MODE_CROSS_ANY_HISTORICAL_FILE: ModeMetadata(
            "...created the file with a copy of a line from any other historical file",
            ["-C"] * 3,
        ),
    }

    # Overrides --------------------------------------------------

    def run(self, edit, mode, permanence):
        if permanence:
            sublime.load_settings(SETTINGS_FILE_BASENAME).set(
                SETTINGS_KEY_COMMIT_SKIPPING_MODE, mode
            )
            sublime.save_settings(SETTINGS_FILE_BASENAME)
            self.view.settings().erase(SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE)
        else:
            self.view.settings().set(SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE, mode)

    def input(self, args):  # noqa: A003
        return ModeInputHandler()


class ModeInputHandler(sublime_plugin.ListInputHandler):

    # Overrides --------------------------------------------------

    def placeholder(self):
        return "Select a mode"

    def list_items(self):
        return [
            [metadata.elaboration, mode]
            if mode == BlameSetCommitSkippingMode.MODE_NONE
            else [
                "{0} (git blame {1})".format(
                    metadata.elaboration, " ".join(metadata.git_args)
                ),
                mode,
            ]
            for mode, metadata in BlameSetCommitSkippingMode.DETAIL.items()
        ]

    def next_input(self, args):
        return PermanenceInputHandler()


class PermanenceInputHandler(sublime_plugin.ListInputHandler):

    # Overrides --------------------------------------------------

    def list_items(self):
        return [
            ("Temporarily (for this open file)", False),
            ("Permanently (a new default will be written to the settings file)", True),
        ]
