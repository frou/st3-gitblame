import threading
import sublime
import sublime_plugin

from .base import BaseBlame
from .templates import blame_inline_phantom_css, blame_inline_phantom_html_template
from .settings import pkg_settings, PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED, PKG_SETTINGS_KEY_INLINE_BLAME_DELAY


class BlameInlineListener(BaseBlame, sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        return pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED)

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, 'git-blame')
        self.timer = None
        self.delay_seconds = pkg_settings().get(PKG_SETTINGS_KEY_INLINE_BLAME_DELAY) / 1000

    def extra_cli_args(self, line_num):
        args = ["-L", "{0},{0}".format(line_num)]
        return args

    def _view(self):
        return self.view

    def show_inline_blame(self):
        phantoms = []
        sels = self.view.sel()
        line = self.view.line(sels[0])
        if line.size() < 2:
            # avoid weird behaviour of regions on empty lines
            # < 2 is to check for newline character (full_line is required)
            return
        pos = line.end()
        row, _ = self.view.rowcol(line.begin())
        anchor = sublime.Region(pos, pos)
        try:
            blame_output = self.get_blame_text(self.view.file_name(), line_num=row + 1)
        except Exception as e:
            return
        blame = next((self.parse_line(line) for line in blame_output.splitlines()), None)
        if not blame:
            return
        body = blame_inline_phantom_html_template.format(
            css=blame_inline_phantom_css,
            author=blame['author'],
            # TODO: add pretty format of the date, like "3 days ago"
            date=blame['date'],
            time=blame['time'] + blame['timezone'],
            # TODO: add first line of the commit here, but
            #       it requires porcelain format of git blame
            #       and further refactoring of BaseBlame
        )
        phantom = sublime.Phantom(anchor, body, sublime.LAYOUT_INLINE)
        phantoms.append(phantom)
        self.phantom_set.update(phantoms)

    def on_selection_modified_async(self):
        self.view.erase_phantoms('git-blame')
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.delay_seconds, self.show_inline_blame)
        self.timer.start()
