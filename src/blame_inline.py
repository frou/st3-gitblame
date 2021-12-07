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


class BlameInlineListener(BaseBlame, sublime_plugin.ViewEventListener):

    pkg_setting_callback_added = False

    # Overrides (ViewEventListener) ----------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, self.phantom_set_key())
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
        self.close_by_user_request()
        self.rerun()

    def on_post_save_async(self):
        self.close_by_user_request()
        # When the file view goes from having unsaved changes to having no unsaved
        # changes, it becomes eligible for Inline Blame to be shown again. Act on that
        # fact now, rather than waiting for the next time the caret gets moved.
        self.rerun()

    # Overrides (BaseBlame) ------------------------------------------------------------

    def extra_cli_args(self, line_num):
        return ["-L", "{0},{0}".format(line_num), "--date=relative"]

    def _view(self):
        return self.view

    def close_by_user_request(self):
        self.view.erase_phantoms(self.phantom_set_key())

    def rerun(self, **kwargs):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay_seconds, self.show_inline_blame)
        self.timer.start()

    # Overrides end --------------------------------------------------------------------

    @classmethod
    def determine_enablement(cls, view_settings):
        enabled = view_settings.get(
            BlameToggleInline.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED
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
            BlameToggleInline.erase_viewlevel_customization(view)
            if not pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED):
                view.erase_phantoms(cls.phantom_set_key())
            # Do a dummy modification to the view's settings to induce the ViewEventListener applicability check to happen again.
            view.settings().set(cls.__name__, "")
            view.settings().erase(cls.__name__)

    def show_inline_blame(self):
        if self.view.is_dirty():
            # If there have already been unsaved edits, stop the git child process from being ran at all.
            return

        phantoms = []

        sels = self.view.sel()
        # @todo Support showing inline blame for multiple carets?
        # @body Maybe with a sanity check that there aren't too many (more than 10?)
        if len(sels) != 1:
            return
        sel0 = sels[0]

        phantom_pos, caret_line_num = self.calculate_positions(sel0)
        if not phantom_pos:
            return

        try:
            blame_output = self.get_blame_text(
                self.view.file_name(), line_num=caret_line_num
            )
        except Exception:  # Don't want to spam Console on failures.
            return

        blame = self.parse_line_with_relative_date(blame_output)
        if not blame or blame["sha"] == "00000000":  # All zeros means uncommited change
            return

        try:
            summary = self.get_commit_message_subject(
                blame["sha"], self.view.file_name()
            )
        except Exception:  # Don't want to spam Console on failures.
            return

        phantom = sublime.Phantom(
            sublime.Region(phantom_pos),
            blame_inline_phantom_html_template.format(
                css=blame_inline_phantom_css,
                author=blame["author"],
                date=blame["relative_date"],
                qs_sha_val=blame["sha"],
                summary_separator=" · " if summary else "",
                summary=summary,
            ),
            sublime.LAYOUT_INLINE,
            self.handle_phantom_button,
        )
        phantoms.append(phantom)

        # Dispatch back onto the main thread to serialize a final is_dirty check.
        sublime.set_timeout(lambda: self.maybe_insert_phantoms(phantoms), 0)

    def calculate_positions(self, user_selection):
        selection_goes_backwards = user_selection.a > user_selection.b

        row, _ = self.view.rowcol(
            user_selection.begin() if selection_goes_backwards else user_selection.end()
        )
        caret_line_num = row + 1

        # Quantise the arbitrary user selection to line(s)
        selection = self.view.line(user_selection)
        if selection.size() <= 1:
            # Not worth showing a blame phantom for an empty line.
            return (None, caret_line_num)

        if selection_goes_backwards:
            phantom_pos = self.view.line(selection.begin()).end()
        else:
            phantom_pos = selection.end()

        return (phantom_pos, caret_line_num)

    def maybe_insert_phantoms(self, phantoms):
        if not self.view.is_dirty():
            self.phantom_set.update(phantoms)


class BlameToggleInline(sublime_plugin.TextCommand):

    # Might as well reuse the same settings key, but at the view-level.
    VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED = PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED

    # Overrides begin ------------------------------------------------------------------

    def run(self, edit):
        enabled = not BlameInlineListener.determine_enablement(self.view.settings())
        if not enabled:
            self.view.erase_phantoms(BlameInlineListener.phantom_set_key())
        self.view.settings().set(self.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED, enabled)

    # Overrides end --------------------------------------------------------------------

    @classmethod
    def erase_viewlevel_customization(cls, view):
        view.settings().erase(cls.VIEW_SETTINGS_KEY_INLINE_BLAME_ENABLED)
