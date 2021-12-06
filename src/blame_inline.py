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

    pkg_setting_callback_added = False

    # Overrides (ViewEventListener) ----------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, INLINE_BLAME_PHANTOM_SET_KEY)
        self.timer = None
        self.delay_seconds = (
            pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_DELAY) / 1000
        )
        # Show it immediately for the initially selected line.
        self.show_inline_blame()

    @classmethod
    def is_applicable(cls, view_settings):
        if not cls.pkg_setting_callback_added:
            pkg_settings().add_on_change(
                PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED,
                cls.on_pkg_setting_changed,
            )
            cls.pkg_setting_callback_added = True

        return cls.determine_enablement(view_settings)

    def on_selection_modified_async(self):
        self.restart_timer()

    def on_post_save_async(self):
        # Redisplay the blame after the file is saved, because there will be
        # no call to on_selection_modified_async after save.
        self.restart_timer()

    # Overrides (BaseBlame) ------------------------------------------------------------

    def extra_cli_args(self, line_num):
        args = ["-L", "{0},{0}".format(line_num), "--date=relative"]
        return args

    def _view(self):
        return self.view

    def close_by_user_request(self):
        # Inline Blame phantoms doesn't have a user-accessible close UI.
        raise NotImplementedError()

    def recurse(self, *args, **kwargs):
        # Inline Blame doesn't need to rerun itself.
        raise NotImplementedError()

    # Overrides end --------------------------------------------------------------------

    @classmethod
    def determine_enablement(cls, view_settings):
        enabled = view_settings.get(
            ToggleInlineGitBlame.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED
        )
        if enabled is None:
            enabled = pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED)
        return enabled

    @classmethod
    def on_pkg_setting_changed(cls):
        # This variable can be elimited once targeting ST4+ only, and the latter lambda body inlined.
        view_is_editor = (
            # REF: https://github.com/sublimehq/sublime_text/issues/3167
            lambda view: not view.settings().get("is_widget")
            if sublime.version().startswith("3")
            else lambda view: view.element() is None
        )
        all_editor_views = [
            view
            for window in sublime.windows()
            for view in window.views()
            if view_is_editor(view)
        ]
        for view in all_editor_views:
            ToggleInlineGitBlame.erase_viewlevel_customization(view)
            if not pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED):
                view.erase_phantoms(INLINE_BLAME_PHANTOM_SET_KEY)
            # Do a dummy modification to the view's settings to induce the ViewEventListener applicability check to happen again.
            view.settings().set(cls.__name__, "")
            view.settings().erase(cls.__name__)

    def restart_timer(self):
        self.view.erase_phantoms(INLINE_BLAME_PHANTOM_SET_KEY)
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay_seconds, self.show_inline_blame)
        self.timer.start()

    def show_inline_blame(self):
        if self.view.is_dirty():
            # If there have already been unsaved edits, stop the git child process from being ran at all.
            return

        phantoms = []
        sels = self.view.sel()
        if len(sels) < 1:
            return

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
            except Exception:
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


class ToggleInlineGitBlame(sublime_plugin.TextCommand):

    # Might as well reuse the same settings key, but at the view-level.
    VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED = PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED

    # Overrides begin ------------------------------------------------------------------

    def run(self, edit):
        enabled = not BlameInlineListener.determine_enablement(self.view.settings())
        if not enabled:
            self.view.erase_phantoms(INLINE_BLAME_PHANTOM_SET_KEY)
        self.view.settings().set(self.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED, enabled)

    # Overrides end --------------------------------------------------------------------

    @classmethod
    def erase_viewlevel_customization(cls, view):
        view.settings().erase(cls.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED)
