import sublime
import sublime_plugin

from .common import *


class BlameSetContentChasingMode(sublime_plugin.TextCommand):
    MODE_NONE = False
    MODE_SAME_FILE_SAME_COMMIT = "same_file_same_commit"
    MODE_CROSS_FILE_SAME_COMMIT = "cross_file_same_commit"
    MODE_CROSS_ANY_FILE = "cross_any_file"
    MODE_CROSS_ANY_HISTORICAL_FILE = "cross_any_historical_file"

    GIT_ARGS_FOR_MODES = {
        MODE_NONE: [],
        MODE_SAME_FILE_SAME_COMMIT: ["-M"],
        MODE_CROSS_FILE_SAME_COMMIT: ["-C"],
        MODE_CROSS_ANY_FILE: ["-C"] * 2,
        MODE_CROSS_ANY_HISTORICAL_FILE: ["-C"] * 3,
    }

    def run(self, edit, mode, permanence):
        if permanence:
            sublime.load_settings(SETTINGS_FILE_BASENAME).set(
                SETTINGS_KEY_CONTENT_CHASING_MODE, mode
            )
            sublime.save_settings(SETTINGS_FILE_BASENAME)
            self.view.settings().erase(SETTINGS_KEY_TEMPORARY_CONTENT_CHASING_MODE)
        else:
            self.view.settings().set(SETTINGS_KEY_TEMPORARY_CONTENT_CHASING_MODE, mode)

    def input(self, args):  # noqa: A003
        return ModeInputHandler()


# TODO: Bump the minimum required Sublime version to the one that introduced *InputHandlers.
# 3.1 (BUILD 3170) https://www.sublimetext.com/3
# https://github.com/wbond/package_control_channel/blob/master/repository/g.json


class ModeInputHandler(sublime_plugin.ListInputHandler):
    def placeholder(self):
        return "Select a mode"

    # TODO: Preselect the mode currently in effect.
    def list_items(self):
        return [
            ["<NONE>", BlameSetContentChasingMode.MODE_NONE],
            BlameSetContentChasingMode.MODE_SAME_FILE_SAME_COMMIT,
            BlameSetContentChasingMode.MODE_CROSS_FILE_SAME_COMMIT,
            BlameSetContentChasingMode.MODE_CROSS_ANY_FILE,
            BlameSetContentChasingMode.MODE_CROSS_ANY_HISTORICAL_FILE,
        ]

    def next_input(self, args):
        return PermanenceInputHandler()

    def description(self, value, text):
        return 'to "{0}"'.format(text)


class PermanenceInputHandler(sublime_plugin.ListInputHandler):
    def list_items(self):
        return [
            ("Temporarily (for this open file)", False),
            ("Permanently (the default in the settings file will be modified)", True),
        ]
