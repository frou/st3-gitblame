import sublime
import sublime_plugin

from .base import BaseBlame
from .templates import blame_all_phantom_css, blame_all_phantom_html_template

PHANTOM_KEY_ALL = "git-blame-all"

VIEW_SETTING_PHANTOM_ALL_DISPLAYED = "git-blame-all-displayed"

VIEW_SETTING_RULERS = "rulers"
VIEW_SETTING_RULERS_PREV = "rulers_prev"


class BlameShowAll(BaseBlame, sublime_plugin.TextCommand):

    HORIZONTAL_SCROLL_DELAY_MS = 100

    # Overrides (TextCommand) ----------------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY_ALL)
        self.pattern = None

    def run(self, edit):
        if not self.has_suitable_view():
            self.tell_user_to_save()
            return

        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        phantoms = []  # type: list[sublime.Phantom] # type: ignore[misc]

        # If they are currently shown, toggle them off and return.
        if self.view.settings().get(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, False):
            self.phantom_set.update(phantoms)
            self.view.settings().erase(VIEW_SETTING_PHANTOM_ALL_DISPLAYED)
            self.view.run_command("blame_restore_rulers")
            # Workaround a visible empty space sometimes remaining in the viewport.
            self.horizontal_scroll_to_limit(left=False)
            self.horizontal_scroll_to_limit(left=True)
            return

        try:
            blame_output = self.get_blame_text(self.view.file_name())
        except Exception as e:
            self.communicate_error(e)
            return

        blames = [self.parse_line(line) for line in blame_output.splitlines()]
        blames = [b for b in blames if b]
        if not blames:
            self.communicate_error(
                "Failed to parse anything for {0}. Has git's output format changed?".format(
                    self.__class__.__name__
                )
            )
            return

        max_author_len = max(len(b["author"]) for b in blames)
        for blame in blames:
            line_number = int(blame["line_number"])
            author = blame["author"]

            phantom = sublime.Phantom(
                self.phantom_region(line_number),
                blame_all_phantom_html_template.format(
                    css=blame_all_phantom_css,
                    sha=blame["sha"],
                    author=author + "&nbsp;" * (max_author_len - len(author)),
                    date=blame["date"],
                    time=blame["time"],
                ),
                sublime.LAYOUT_INLINE,
                self.handle_phantom_button,
            )
            phantoms.append(phantom)

        self.phantom_set.update(phantoms)
        self.view.settings().set(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, True)
        self.store_rulers()
        # Bring the phantoms into view without the user needing to manually scroll left.
        self.horizontal_scroll_to_limit(left=True)

    # Overrides (BaseBlame) ------------------------------------------------------------

    def _view(self):
        return self.view

    def extra_cli_args(self, **kwargs):
        return []

    def close_by_user_request(self):
        self.view.run_command("blame_erase_all")

    def recurse(self, *args, **kwargs):
        # BlameAll doesn't need to rerun itself.
        raise NotImplementedError()

    # Overrides end --------------------------------------------------------------------

    def phantom_region(self, line_number):
        line_begins_pt = self.view.text_point(line_number - 1, 0)
        return sublime.Region(line_begins_pt)

    def store_rulers(self):
        self.view.settings().set(
            VIEW_SETTING_RULERS_PREV,
            self.view.settings().get(VIEW_SETTING_RULERS),
        )
        self.view.settings().set(VIEW_SETTING_RULERS, [])

    def horizontal_scroll_to_limit(self, *, left):
        x = 0.0 if left else self.view.layout_extent()[0]
        y = self.view.viewport_position()[1]
        # NOTE: The scrolling doesn't seem to work if called inline (or with a 0ms timeout).
        sublime.set_timeout(
            lambda: self.view.set_viewport_position((x, y)),
            self.HORIZONTAL_SCROLL_DELAY_MS,
        )


class BlameEraseAll(sublime_plugin.TextCommand):

    # Overrides begin ------------------------------------------------------------------

    def run(self, edit):
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        self.view.settings().erase(VIEW_SETTING_PHANTOM_ALL_DISPLAYED)
        self.view.run_command("blame_restore_rulers")

    # Overrides end --------------------------------------------------------------------


class BlameEraseAllListener(sublime_plugin.ViewEventListener):

    # Overrides begin ------------------------------------------------------------------

    @classmethod
    def is_applicable(cls, settings):
        return settings.get(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, False)

    def on_modified_async(self):
        self.view.run_command("blame_erase_all")

    # Overrides end --------------------------------------------------------------------


class BlameRestoreRulers(sublime_plugin.TextCommand):

    # Overrides begin ------------------------------------------------------------------

    def run(self, edit):
        self.view.settings().set(
            VIEW_SETTING_RULERS,
            self.view.settings().get(VIEW_SETTING_RULERS_PREV),
        )

    # Overrides end --------------------------------------------------------------------
