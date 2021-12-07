from urllib.parse import quote_plus

import sublime_plugin

from .base import BaseBlame


class BlameInstadiff(BaseBlame, sublime_plugin.TextCommand):

    # Overrides (TextCommand) ----------------------------------------------------------

    def run(self, edit):
        if not self.has_suitable_view():
            self.tell_user_to_save()
            return

        if len(self.view.sel()) != 1:
            self.communicate_error(
                "{0} requires there to be exactly 1 selection".format(
                    self.__class__.__name__
                )
            )
            return
        sel0 = self.view.sel()[0]

        row_num, _ = self.view.rowcol(sel0.begin())
        line_num = row_num + 1
        try:
            blame_output = self.get_blame_text(self.view.file_name(), line_num=line_num)
        except Exception as e:
            self.communicate_error(e)
            return

        blame = self.parse_line(blame_output)
        if not blame:
            self.communicate_error(
                "Failed to parse anything for {0}. Has git's output format changed?".format(
                    self.__class__.__name__
                )
            )
            return

        href = "show?sha={0}".format(quote_plus(blame["sha_normalised"]))
        self.handle_phantom_button(href)

    # Overrides (BaseBlame) ------------------------------------------------------------

    def _view(self):
        return self.view

    def close_by_user_request(self):
        raise NotImplementedError()

    def extra_cli_args(self, line_num):
        return ["-L", "{0},{0}".format(line_num)]

    def rerun(self, **kwargs):
        self.run(None)

    # Overrides end --------------------------------------------------------------------
