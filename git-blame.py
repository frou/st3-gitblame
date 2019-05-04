import sublime
import sublime_plugin
import os
import re
import subprocess

PHANTOM_KEY_ALL = 'git-blame-all'
SETTING_PHANTOM_ALL_DISPLAYED = 'git-blame-all-displayed'

stylesheet_one = '''
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

template_one = '''
    <body id="inline-git-blame">
        {stylesheet}
        <div class="phantom-arrow"></div>
        <div class="phantom">
            <span class="message">
                <strong>Git Blame</strong> ({user})
                {date} {time} |
                {sha}
                <a href="copy-{sha}">[Copy]</a>
                <a href="show-{sha}">[Show]</a>
                <a class="close" href="close">''' + chr(0x00D7) + '''</a>
            </span>
        </div>
    </body>
'''

stylesheet_all = '''
    <style>
        div.phantom {
            padding: 0;
            margin: 0;
            background-color: color(var(--bluish) blend(var(--background) 30%));
        }
        div.phantom .user {
            width: 10em;
        }
        div.phantom a.close {
            padding: 0.35rem 0.7rem 0.45rem 0.8rem;
            position: relative;
            bottom: 0.05rem;
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

template_all = '''
    <body id="inline-git-blame">
        {stylesheet}
        <div class="phantom">
            <span class="message">
                {sha} (<span class="user">{user}</span> {date} {time})
                <a class="close" href="close">''' + chr(0x00D7) + '''</a>
            </span>
        </div>
    </body>
'''

# Sometimes this fails on other OS, just error silently
try:
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
except Exception:
    si = None


class BlameCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        self.view = view
        self.phantom_set = sublime.PhantomSet(view, 'git-blame')

    def get_blame(self, line, path):
        return subprocess.check_output(
            ["git", "blame", "--minimal", "-w", "-L {0},{0}".format(line), os.path.basename(path)],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT
        ).decode("utf-8")

    def parse_blame(self, blame):
        sha, file_path, user, date, time, tz_offset, *_ = blame.split()

        # Was part of the inital commit so no updates
        if file_path[0] == '(':
            user, date, time, tz_offset = file_path, user, date, time
            file_path = None

        # Fix an issue where the username has a space
        # Im going to need to do something better though if people
        # start to have multiple spaces in their names.
        if not date[0].isdigit():
            user = "{0} {1}".format(user, date)
            date, time = time, tz_offset

        return(sha, user[1:], date, time)

    def get_commit(self, sha, path):
        return subprocess.check_output(
            ["git", "show", sha],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT
        ).decode('utf-8')

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
                try:
                    desc = self.get_commit(sha, self.view.file_name())
                except Exception as e:
                    communicate_error(e)
                    return

                buf = self.view.window().new_file()
                buf.run_command('insert_commit_description', {'desc': desc, 'scratch_view_name': 'commit ' + sha})
            else:
                self.view.erase_phantoms('git-blame')
        else:
            self.view.erase_phantoms('git-blame')

    def run(self, edit):
        if not view_is_suitable(self.view):
            return

        phantoms = []
        self.view.erase_phantoms('git-blame')
        # Before adding the phantom, see if the current phantom that is displayed is at the same spot at the selection
        if self.phantom_set.phantoms:
            phantom_exists = self.view.line(self.view.sel()[0]) == self.view.line(self.phantom_set.phantoms[0].region)
            if phantom_exists:
                self.phantom_set.update(phantoms)
                return

        for region in self.view.sel():
            line = self.view.line(region)
            (row, col) = self.view.rowcol(region.begin())
            full_path = self.view.file_name()

            try:
                blame_output = self.get_blame(int(row) + 1, full_path)
            except Exception as e:
                communicate_error(e)
                return

            sha, user, date, time = self.parse_blame(blame_output)

            body = template_one.format(sha=sha, user=user, date=date, time=time, stylesheet=stylesheet_one)

            phantom = sublime.Phantom(line, body, sublime.LAYOUT_BLOCK, self.on_phantom_close)
            phantoms.append(phantom)
        self.phantom_set.update(phantoms)


class BlameShowAllCommand(sublime_plugin.TextCommand):

    # The fixed length for author names
    NAME_LENGTH = 10

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY_ALL)
        self.pattern = None

    def run(self, edit):
        if not view_is_suitable(self.view):
            return

        self.view.erase_phantoms(PHANTOM_KEY_ALL)
        phantoms = []

        # If they are currently shown, toggle them off and return.
        if self.view.settings().get(SETTING_PHANTOM_ALL_DISPLAYED, False):
            self.phantom_set.update(phantoms)
            self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, False)
            return

        try:
            blame_output = self.get_blame(self.view.file_name())
        except Exception as e:
            communicate_error(e)
            return

        for l in blame_output.splitlines():
            parsed = self.parse_blame(l)
            if not parsed:
                continue

            sha, author, date, time, line_number = parsed

            body = template_all.format(sha=sha,
                                       user=self.format_name(author),
                                       date=date,
                                       time=time,
                                       stylesheet=stylesheet_all)

            line_point = self.get_line_point(line_number - 1)
            phantom = sublime.Phantom(line_point,
                                      body,
                                      sublime.LAYOUT_INLINE,
                                      self.on_phantom_close)
            phantoms.append(phantom)

        self.phantom_set.update(phantoms)
        self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, True)
        # Bring the phantoms into view without the user needing to manually scroll left.
        self.view.set_viewport_position((0.0, self.view.viewport_position()[1]))

    def get_blame(self, path):
        return subprocess.check_output(
            # The option --show-name is necessary to force file name display.
            ["git", "blame", "--show-name", "--minimal", "-w", os.path.basename(path)],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT
        ).decode("utf-8")

    def parse_blame(self, blame):
        '''Parses git blame output.
        '''
        if not self.pattern:
            self.prepare_pattern()

        m = self.pattern.match(blame)
        if m:
            sha = m.group('sha')
            # Currently file is not used.
            # file = m.group('file')
            author = m.group('author')
            date = m.group('date')
            time = m.group('time')
            line_number = int(m.group('line_number'))
            return sha, author, date, time, line_number
        else:
            return None

    def prepare_pattern(self):
        '''Prepares the regex pattern to parse git blame output.
        '''
        # The SHA output by git-blame may have a leading caret to indicate
        # that it is a "boundary commit".
        p_sha = r'(?P<sha>\^?\w+)'
        p_file = r'((?P<file>[\S ]+)\s+)'
        p_author = r'(?P<author>.+?)'
        p_date = r'(?P<date>\d{4}-\d{2}-\d{2})'
        p_time = r'(?P<time>\d{2}:\d{2}:\d{2})'
        p_timezone = r'(?P<timezone>[\+-]\d+)'
        p_line = r'(?P<line_number>\d+)'
        s = r'\s+'

        self.pattern = re.compile(r'^' + p_sha + s + p_file + r'\(' +
                                  p_author + s + p_date + s + p_time + s +
                                  p_timezone + s + p_line + r'\) ')

    def format_name(self, name):
        '''Formats author names so that widths of phantoms become equal.
        '''
        ellipsis = '...'
        if len(name) > self.NAME_LENGTH:
            return name[:self.NAME_LENGTH] + ellipsis
        else:
            return name + '.' * (self.NAME_LENGTH - len(name)) + ellipsis

    def get_line_point(self, line):
        '''Get the point of specified line in a view.
        '''
        return self.view.line(self.view.text_point(line, 0))

    def on_phantom_close(self, href):
        '''Closes opened phantoms.
        '''
        if href == 'close':
            self.view.run_command('blame_erase_all')


class BlameEraseAllCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        '''Erases the blame results.
        '''
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)


class BlameEraseAllListener(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        '''Checks if the blame_erase_all command is applicable.
        '''
        return settings.get(SETTING_PHANTOM_ALL_DISPLAYED, False)

    def on_modified_async(self):
        '''Automatically erases the blame results to prevent mismatches.
        '''
        self.view.run_command('blame_erase_all')
        self.view.settings().erase(SETTING_PHANTOM_ALL_DISPLAYED)


class InsertCommitDescriptionCommand(sublime_plugin.TextCommand):

    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.set_syntax_file('Packages/Diff/Diff.sublime-syntax')
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)


def view_is_suitable(view):
    ok = view.file_name() and not view.is_dirty()
    if not ok:
        communicate_error("Please save file changes to disk first.")
    return ok


def communicate_error(e, modal=True):
    user_msg = "Git blame:\n\n{}".format(e)
    if isinstance(e, subprocess.CalledProcessError):
        user_msg += "\n\n{}".format(e.output.decode("utf-8"))

    print()
    if modal:
        sublime.error_message(user_msg)
    else:
        sublime.status_message(user_msg)
        # Unlike with the error dialog, a status message is not automatically
        # persisted in the console too.
        print(user_msg)
