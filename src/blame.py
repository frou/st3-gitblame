from urllib.parse import quote_plus

import sublime
import sublime_plugin

from .base import BaseBlame
from .templates import blame_phantom_css, blame_phantom_html_template


class Blame(BaseBlame, sublime_plugin.TextCommand):

    # Overrides (TextCommand) ----------------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, self.phantom_set_key())

    def run(self, edit, prevving=False, fixed_row_num=None, sha_skip_list=[]):
        if not self.has_suitable_view():
            self.tell_user_to_save()
            return

        phantoms = []

        if prevving:
            # We'll be getting blame information for the line whose existing phantom's
            # [Prev] button was clicked, regardless of where the text cursor(s)
            # currently are.
            relevant_regions = [sublime.Region(self.view.text_point(fixed_row_num, 0))]
        else:
            # We'll be getting blame information for the lines where text cursor(s)
            # currently are.
            relevant_regions = self.view.sel()

        for region in relevant_regions:
            line_region = self.view.line(region)

            # When this Command is ran for a line with a phantom already visible, we
            # erase the phantom (i.e. toggle it). But if the reason this Command is
            # being ran is because the user is clicking the [Prev] button, just erasing
            # the existing phantom is not sufficient, because we need to then display
            # another phantom with updated content.
            if self.phantom_exists_for_region(line_region) and not prevving:
                continue

            row_num, _ = self.view.rowcol(region.begin())
            line_num = row_num + 1

            full_path = self.view.file_name()

            try:
                blame_output = self.get_blame_text(
                    full_path, line_num=line_num, sha_skip_list=sha_skip_list
                )
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
            sha = blame["sha"]
            sha_normalised = blame["sha_normalised"]
            author = blame["author"]
            date = blame["date"]
            time = blame["time"]

            if sha_skip_list:
                recently_skipped_sha = sha_skip_list[-1]
                if sha_normalised == recently_skipped_sha:
                    sublime.message_dialog(
                        "No earlier commits affected line {0}".format(line_num)
                    )
                    return

            phantoms.append(
                sublime.Phantom(
                    line_region,
                    blame_phantom_html_template.format(
                        css=blame_phantom_css,
                        sha=sha,
                        sha_not_latest_indicator=" *" if sha_skip_list else "",
                        author=author,
                        date=date,
                        time=time,
                        qs_row_num_val=quote_plus(str(row_num)),
                        qs_sha_val=quote_plus(sha_normalised),
                        # Querystrings can contain the same key multiple times. We use that
                        # functionality to accumulate a list of SHAs to skip over when
                        # a [Prev] button has been clicked multiple times.
                        qs_skip_keyvals="&amp;".join(
                            [
                                "skip={0}".format(quote_plus(skipee))
                                for skipee in sha_skip_list
                            ]
                        ),
                    ),
                    sublime.LAYOUT_BLOCK,
                    self.handle_phantom_button,
                )
            )

        self.phantom_set.update(phantoms)

    # Overrides (BaseBlame) ------------------------------------------------------------

    def _view(self):
        return self.view

    def close_by_user_request(self):
        self.phantom_set.update([])

    def extra_cli_args(self, line_num, sha_skip_list):
        args = ["-L", "{0},{0}".format(line_num)]
        for skipped_sha in sha_skip_list:
            args.extend(["--ignore-rev", skipped_sha])
        return args

    def rerun(self, **kwargs):
        self.run(None, **kwargs)

    # Overrides end --------------------------------------------------------------------

    def phantom_exists_for_region(self, region):
        return any(p.region == region for p in self.phantom_set.phantoms)


class BlameInsertCommitDescription(sublime_plugin.TextCommand):

    # Overrides begin ------------------------------------------------------------------

    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.assign_syntax("Packages/Diff/Diff.sublime-syntax")
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)
        view.set_read_only(True)

    # Overrides end --------------------------------------------------------------------
