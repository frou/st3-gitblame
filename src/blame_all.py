import sublime
import sublime_plugin

from .base import BaseBlame
from .templates import blame_all_phantom_css, blame_all_phantom_html_template

PHANTOM_KEY_ALL = "git-blame-all"

VIEW_SETTING_PHANTOM_ALL_DISPLAYED = "git-blame-all-displayed"

VIEW_SETTING_RULERS = "rulers"
VIEW_SETTING_RULERS_PREV = "rulers_prev"

# @todo Disable view rulers while BlameAll phantoms are visible
# @body Because they don't make sense while a big blob of phantoms are horizontally offsetting the user's code.


class BlameShowAll(BaseBlame, sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY_ALL)
        self.pattern = None

    def run(self, edit):
        if not self.has_suitable_view():
            self.tell_user_to_save()
            return

        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        phantoms = []  # type: list[sublime.Phantom]

        # If they are currently shown, toggle them off and return.
        if self.view.settings().get(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, False):
            self.phantom_set.update(phantoms)
            self.view.settings().set(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, False)
            self.view.run_command("blame_restore_rulers")
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
            line_point = self.get_line_point(line_number - 1)

            author = blame["author"]

            phantom = sublime.Phantom(
                line_point,
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
        # @todo BlameAll: Automatically scrolling the view to the left doesn't work when the ST window has >1 Group
        self.view.set_viewport_position((0.0, self.view.viewport_position()[1]))

    def extra_cli_args(self, **kwargs):
        return []

    # ------------------------------------------------------------

    def handle_phantom_button(self, href):
        if href == "close":
            self.view.run_command("blame_erase_all")

    def get_line_point(self, line):
        """Get the point of specified line in a view."""
        return self.view.line(self.view.text_point(line, 0))

    def store_rulers(self):
        self.view.settings().set(
            VIEW_SETTING_RULERS_PREV,
            self.view.settings().get(VIEW_SETTING_RULERS),
        )
        self.view.settings().set(VIEW_SETTING_RULERS, [])


class BlameEraseAll(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def run(self, edit):
        """Erases the blame results."""
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        self.view.run_command("blame_restore_rulers")


class BlameEraseAllListener(sublime_plugin.ViewEventListener):

    # Overrides --------------------------------------------------

    @classmethod
    def is_applicable(cls, settings):
        """Checks if the blame_erase_all command is applicable."""
        return settings.get(VIEW_SETTING_PHANTOM_ALL_DISPLAYED, False)

    def on_modified_async(self):
        """Automatically erases the blame results to prevent mismatches."""
        self.view.run_command("blame_erase_all")
        self.view.settings().erase(VIEW_SETTING_PHANTOM_ALL_DISPLAYED)


class BlameRestoreRulers(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def run(self, edit):
        self.view.settings().set(
            VIEW_SETTING_RULERS,
            self.view.settings().get(VIEW_SETTING_RULERS_PREV),
        )
