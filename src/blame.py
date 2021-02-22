from urllib.parse import parse_qs, quote_plus, urlparse

import sublime
import sublime_plugin

from .base_blame import BaseBlame
from .parsing import parse_blame_cli_output_line
from .templates import blame_phantom_css, blame_phantom_html_template

# @todo Make a command to open the latest diff ("CommitDescription") for the current line in a single keystroke.
# @body Currently it takes a keystroke and then a mouse click on "Show"


class Blame(BaseBlame, sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(view, "git-blame")

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
                blame_output = self.get_blame(
                    full_path, line_num=line_num, sha_skip_list=sha_skip_list
                )
            except Exception as e:
                self.communicate_error(e)
                return

            blame = parse_blame_cli_output_line(blame_output)
            if not blame:
                self.communicate_error(
                    "Failed to parse anything for {0}. Has git's output format changed?".format(
                        self.__class__.__name__
                    )
                )
                return
            sha = blame["sha"]
            author = blame["author"]
            date = blame["date"]
            time = blame["time"]

            # The SHA output by `git blame` may have a leading caret to indicate that it
            # is a "boundary commit". That needs to be stripped before passing the SHA
            # back to git CLI commands for other purposes.
            sha_normalised = sha.strip("^")

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

    def extra_cli_args(self, line_num, sha_skip_list):
        args = ["-L", "{0},{0}".format(line_num)]
        for skipped_sha in sha_skip_list:
            args.extend(["--ignore-rev", skipped_sha])
        return args

    # ------------------------------------------------------------

    def phantom_exists_for_region(self, region):
        return any(p.region == region for p in self.phantom_set.phantoms)

    def handle_phantom_button(self, href):
        url = urlparse(href)
        querystring = parse_qs(url.query)
        # print(url)
        # print(querystring)

        if url.path == "copy":
            sublime.set_clipboard(querystring["sha"][0])
            sublime.status_message("Git SHA copied to clipboard")
        elif url.path == "show":
            sha = querystring["sha"][0]
            try:
                desc = self.get_commit(sha, self.view.file_name())
            except Exception as e:
                self.communicate_error(e)
                return

            buf = self.view.window().new_file()
            buf.run_command(
                "blame_insert_commit_description",
                {"desc": desc, "scratch_view_name": "commit " + sha},
            )
        elif url.path == "prev":
            sha = querystring["sha"][0]
            row_num = querystring["row_num"][0]
            sha_skip_list = querystring.get("skip", [])
            if sha not in sha_skip_list:
                sha_skip_list.append(sha)
            self.run(
                None,
                prevving=True,
                fixed_row_num=int(row_num),
                sha_skip_list=sha_skip_list,
            )
        elif url.path == "close":
            # Erase all phantoms
            self.phantom_set.update([])
        else:
            self.communicate_error(
                "No handler for URL path '{0}' in phantom".format(url.path)
            )


class BlameInsertCommitDescription(sublime_plugin.TextCommand):

    # Overrides --------------------------------------------------

    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.assign_syntax("Packages/Diff/Diff.sublime-syntax")
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)
        view.set_read_only(True)
