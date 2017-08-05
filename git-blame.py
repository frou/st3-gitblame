import sublime
import sublime_plugin
import os
import functools
import subprocess
from subprocess import check_output as shell

stylesheet = '''
    <style>
        div.phantom-arrow {
            border-top: 0.4rem solid transparent;
            border-left: 0.5rem solid color(var(--bluish) blend(var(--background) 30%));
            width: 0;
            height: 0;
        }
        div.phantom {
            padding: 0.4rem 0 0.4rem 0.7rem;
            margin: 0 0 0.2rem;
            border-radius: 0 0.2rem 0.2rem 0.2rem;
            background-color: color(var(--bluish) blend(var(--background) 30%));
        }
        div.phantom span.message {
            padding-right: 0.7rem;
        }
        div.phantom a {
            text-decoration: inherit;
        }
        div.phantom a.close {
            padding: 0.35rem 0.7rem 0.45rem 0.8rem;
            position: relative;
            bottom: 0.05rem;
            border-radius: 0 0.2rem 0.2rem 0;
            font-weight: bold;
        }
        html.dark div.phantom a.close {
            background-color: #00000018;
        }
        html.light div.phantom a.close {
            background-color: #ffffff18;
        }
    </style>
'''

template = '''
    <body id="inline-git-blame">
        {stylesheet}
        <div class="phantom-arrow"></div>
        <div class="phantom">
            <span class="message">
                <strong>Git Blame:</strong> ({user})
                Updated: {date} {time} |
                {sha}
                <a href="copy-{sha}">[Copy]</a>
                <a href="show-{sha}">[Show]</a>
                <a class="close" href="close">''' + chr(0x00D7) + '''</a>
            </span>
        </div>
    </body>
'''

# Sometimes this fails on other OS, just error silently
try:
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
except:
    si = None

class BlameCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        self.view = view
        self.phantom_set = sublime.PhantomSet(view, 'git-blame')

    @functools.lru_cache(128, False)
    def get_blame(self, line, path):
        try:
            return shell(["git", "blame", "--minimal", "-w",
                "-L {0},{0}".format(line), path],
                cwd=os.path.dirname(os.path.realpath(path)),
                startupinfo=si,
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("Git blame: git error {}:\n{}".format(e.returncode, e.output.decode("UTF-8")))
        except Exception as e:
            print("Git blame: Unexpected error:", e)

    def parse_blame(self, blame):
        sha, file_path, user, date, time, tz_offset, *_ = blame.decode('utf-8').split()

        # Was part of the inital commit so no updates
        if file_path[0] == '(':
            user, date, time, tz_offset = file_path, user, date, time
            file_path = None

        # Fix an issue where the username has a space
        # Im going to need to do something better though if people
        # start to have multiple spaces in their names.
        if not isinstance(date[0], int):
            user = "{0} {1}".format(user, date)
            date, time = time, tz_offset

        return(sha, user[1:], date, time)

    def get_commit(self, sha, path):
        try:
            return shell(["git", "show", sha],
                cwd=os.path.dirname(os.path.realpath(path)),
                startupinfo=si)
        except Exception as e:
            return

    def on_phantom_close(self, href):
        href_parts = href.split('-')

        if len(href_parts) > 1:
            intent = href_parts[0]
            sha = href_parts[1]
            # The SHA output by git-blame may have a leading caret to indicate
            # that it is a "boundary commit". That useful information has
            # already been shown in the phantom, so strip it before going on to
            # use the SHA programmatically.
            sha = sha.strip('^')

            if intent == "copy":
                sublime.set_clipboard(sha)
                sublime.status_message('Git SHA copied to clipboard')
            elif intent == "show":
                desc = self.get_commit(sha, self.view.file_name()).decode('utf-8')
                buf = self.view.window().new_file()
                buf.run_command('insert_commit_description', {'desc': desc})
            else:
                self.view.erase_phantoms('git-blame')
        else:
            self.view.erase_phantoms('git-blame')

    def run(self, edit):
        phantoms = []
        self.view.erase_phantoms('git-blame')

        for region in self.view.sel():
            line = self.view.line(region)
            (row, col) = self.view.rowcol(region.begin())
            full_path = self.view.file_name()
            result = self.get_blame(int(row) + 1, full_path)
            if not result:
                # Unable to get blame
                return

            sha, user, date, time = self.parse_blame(result)

            body = template.format(sha=sha, user=user, date=date, time=time, stylesheet=stylesheet)

            phantom = sublime.Phantom(line, body, sublime.LAYOUT_BLOCK, self.on_phantom_close)
            phantoms.append(phantom)
        self.phantom_set.update(phantoms)


class InsertCommitDescriptionCommand(sublime_plugin.TextCommand):

    def run(self, edit, desc):
        view = self.view
        view.set_scratch(True)
        view.set_syntax_file('Packages/Diff/Diff.sublime-syntax')
        view.insert(edit, 0, desc)

