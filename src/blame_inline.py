import threading

import sublime
import sublime_plugin

from .base import BaseBlame
from .settings import (
    PKG_SETTINGS_KEY_INLINE_BLAME_DELAY,
    PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED,
    pkg_settings,
)
from .templates import blame_inline_phantom_css, blame_inline_phantom_html_template

INLINE_BLAME_PHANTOM_SET_KEY = "git-blame-inline"


class BlameInlineListener(BaseBlame, sublime_plugin.ViewEventListener):
    @classmethod
    def is_applicable(cls, settings):
        # @todo Fix inline blame (sometimes?) remaining enabled when the user setting for it is edited from true -> false
        return pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED)

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, INLINE_BLAME_PHANTOM_SET_KEY)
        self.timer = None
        self.delay_seconds = (
            pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_DELAY) / 1000
        )

    def extra_cli_args(self, line_num):
        args = ["-L", "{0},{0}".format(line_num), "--date=relative"]
        return args

    def _view(self):
        return self.view

    def show_inline_blame(self):
        if self.view.is_dirty():
            # If there have already been unsaved edits, stop the git child process from being ran at all.
            return

        phantoms = []
        sels = self.view.sel()
        # @todo Support showing inline blame for multiple carets?
        # @body Maybe with a sanity check that there aren't too many (more than 10?)
        line = self.view.line(sels[0])
        if line.size() < 2:
            # avoid weird behaviour of regions on empty lines
            # < 2 is to check for newline character
            return
        pos = line.end()
        row, _ = self.view.rowcol(line.begin())
        anchor = sublime.Region(pos, pos)
        try:
            blame_output = self.get_blame_text(self.view.file_name(), line_num=row + 1)
        except Exception:
            return
        blame = next(
            (
                self.parse_line_with_relative_date(line)
                for line in blame_output.splitlines()
            ),
            None,
        )
        if not blame:
            return
        summary = ""
        # Uncommitted changes have only zeros in sha
        if blame["sha"] != "00000000":
            try:
                summary = self.get_commit_message_first_line(
                    blame["sha"], self.view.file_name()
                )
            except Exception as e:
                return
        body = blame_inline_phantom_html_template.format(
            css=blame_inline_phantom_css,
            author=blame["author"],
            date=blame["relative_date"],
            qs_sha_val=blame["sha"],
            summary_separator=" · " if summary else "",
            summary=summary,
        )
        phantom = sublime.Phantom(
            anchor, body, sublime.LAYOUT_INLINE, self.handle_phantom_button
        )
        phantoms.append(phantom)

        # Dispatch back onto the main thread to serialize a final is_dirty check.
        sublime.set_timeout(lambda: self.maybe_insert_phantoms(phantoms), 0)

    def maybe_insert_phantoms(self, phantoms):
        if not self.view.is_dirty():
            self.phantom_set.update(phantoms)

    def show_inline_blame_handler(self):
        self.view.erase_phantoms(INLINE_BLAME_PHANTOM_SET_KEY)
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay_seconds, self.show_inline_blame)
        self.timer.start()

    def on_selection_modified_async(self):
        self.show_inline_blame_handler()

    def on_post_save_async(self):
        # Redisplay the blame after the file is saved, because there will be
        # no call to on_selection_modified_async after save.
        self.show_inline_blame_handler()
