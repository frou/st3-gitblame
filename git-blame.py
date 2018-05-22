import sublime
import sublime_plugin
import os
import re
import functools
import subprocess
from subprocess import check_output as shell

PHANTOM_KEY_ALL = 'git-blame-all'
SETTING_PHANTOM_ALL_DISPLAYED = 'git-blame-all-displayed'
SETTING_SHOW_BLAME_INLINE = 'git-blame-show-inline'

stylesheet_one_inline = '''
<style>
div.phantom {
    padding-left: 2rem;
    color: color(var(--bluish) blend(var(--background) 30%));
}

div.phantom span.message {
    padding-right: 0.7rem;
    padding-left: 0.7rem;
}
div.phantom a {
    text-decoration: inherit;
    color: color(var(--bluish) blend(var(--background) 60%));
}
div.phantom a.close {
    display: none;

}
</style>
'''

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


p_sha = r'(?P<sha>\^?\w+)'
p_file = r'((?P<file>[\S ]+)\s+)'
p_author = r'(?P<author>.+?)'
p_date = r'(?P<date>\d{4}-\d{2}-\d{2})'
p_time = r'(?P<time>\d{2}:\d{2}:\d{2})'
p_timezone = r'(?P<timezone>[\+-]\d+)'
p_line = r'(?P<line_number>\d+)'
s = r'\s+'

r_pattern = re.compile(r'^{sha}{s}{file}\({author}{s}{date}{s}{time}{s}{timezone}{s}{line}\)'.format(
    s=s,
    sha=p_sha,
    file=p_file,
    author=p_author,
    date=p_date,
    time=p_time,
    timezone=p_timezone,
    line=p_line
))


@functools.lru_cache(256, False)
def get_blame(line, path):
    '''Run `git blame` for a specific line.
    '''
    try:
        command = ["git", "blame", "--show-name", "--minimal", "-w", "-L {0},{0}".format(line), path]
        output = shell(
            command,
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT
        )
        return output.decode('UTF-8')
    except subprocess.CalledProcessError as e:
        print("Git blame: git error {}:\n{}".format(e.returncode, e.output.decode("UTF-8")))
    except Exception as e:
        print("Git blame: Unexpected error:", e)


@functools.lru_cache(256, False)
def get_blame_lines(path):
    '''Run `git blame` and get the output lines.
    '''
    try:
        # The option --show-name is necessary to force file name display.
        command = ["git", "blame", "--show-name", "--minimal", "-w", path]
        output = shell(
            command,
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si,
            stderr=subprocess.STDOUT
        )
        return output.decode("UTF-8").splitlines()
    except subprocess.CalledProcessError as e:
        print("Git blame: git error {}:\n{}".format(e.returncode, e.output.decode("UTF-8")))
    except Exception as e:
        print("Git blame: Unexpected error:", e)


@functools.lru_cache(256, False)
def get_commit(sha, path):
    '''Run `git show` and return the direct output.
    '''
    try:
        return shell(
            ["git", "show", sha],
            cwd=os.path.dirname(os.path.realpath(path)),
            startupinfo=si
        )
    except Exception as e:
        return


@functools.lru_cache(128, False)
def parse_blame(blame):
        '''Parses git blame output.
        '''

        # Maybe i dont know
        try:
            blame = blame.decode('UTF-8')
        except:
            pass

        m = r_pattern.match(blame)
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


class BasePlugin(sublime_plugin.ViewEventListener, sublime_plugin.TextCommand):
    PHANTOM_KEY = 'git-blame'

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, self.PHANTOM_KEY)

    def on_phantom_close(self, href):
        '''Closes opened phantoms.
        '''
        if href == 'close':
            self.view.run_command(self.PHANTOM_KEY)

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
                desc = get_commit(sha, self.view.file_name()).decode('utf-8')
                buf = self.view.window().new_file()
                buf.run_command('insert_commit_description', {'desc': desc, 'scratch_view_name': 'commit ' + sha})
            else:
                self.view.erase_phantoms(self.PHANTOM_KEY)
        else:
            self.view.erase_phantoms(self.PHANTOM_KEY)


class BlameCommand(BasePlugin):
    PHANTOM_KEY = 'git-blame'

    def run(self, edit):
        if self.view.is_dirty():
            sublime.status_message("The file needs to be saved for git blame.")
            return

        phantoms = []
        self.view.erase_phantoms(self.PHANTOM_KEY)
        # Before adding the phantom, see if the current phantom that is displayed is at the same spot at the selection
        phantom_exists = self.view.line(self.view.sel()[0]) == self.view.line(self.phantom_set.phantoms[0].region)
        if self.phantom_set.phantoms and phantom_exists:
            self.phantom_set.update(phantoms)
            return

        for region in self.view.sel():
            line = self.view.line(region)
            (row, col) = self.view.rowcol(region.begin())
            full_path = self.view.file_name()
            result = get_blame(int(row) + 1, full_path)
            if not result:
                # Unable to get blame
                return

            parsed = parse_blame(result)
            if not parsed:
                continue

            sha, user, date, time, line_no = parsed

            body = template_one.format(sha=sha, user=user, date=date, time=time, stylesheet=stylesheet_one)

            pos = line.end()
            anchor = sublime.Region(pos, pos)
            phantom = sublime.Phantom(anchor, body, sublime.LAYOUT_BLOCK, self.on_phantom_close)
            phantoms.append(phantom)
        self.phantom_set.update(phantoms)


class BlameInlineEvent(BasePlugin):
    PHANTOM_KEY = 'git-blame-inline'

    @classmethod
    def is_applicable(cls, settings):
        '''Checks if the blame_erase_all command is applicable.
        '''
        return settings.get(SETTING_SHOW_BLAME_INLINE, False)

    def on_selection_modified_async(self):

        self.view.erase_phantoms(self.PHANTOM_KEY)
        if not self.view.settings().get(SETTING_SHOW_BLAME_INLINE, False):
            return
        phantoms = []
        # get selected regions as RegionSet
        sels = self.view.sel()
        for region in sels:

            # get the current line
            lines = self.view.lines(region)
            for line in lines:
                line = self.view.line(line)
                if line.size() == 0:
                    continue

                # get row, col
                row, col = self.view.rowcol(region.begin())
                full_path = self.view.file_name()
                result = get_blame(int(row) + 1, full_path)
                if not result:
                    # Unable to get blame
                    return

                parsed = parse_blame(result)
                if not parsed:
                    continue

                sha, user, date, time, line_no = parsed

                # pos = line.begin() + 80 if line.size() < 80 else line.end()
                pos = line.end() + 1 if line.size() == 0 else line.end()
                anchor = sublime.Region(pos, pos)
                body = template_one.format(sha=sha, user=user, date=date, time=time, stylesheet=stylesheet_one_inline)

                phantom = sublime.Phantom(anchor, body, sublime.LAYOUT_INLINE, self.on_phantom_close)
                phantoms.append(phantom)
        self.phantom_set.update(phantoms)


class BlameToggleInlineCommand(BasePlugin):
    PHANTOM_KEY = 'git-blame-inline'

    def run(self, edit):
        # Clean up old phantoms
        self.view.erase_phantoms(self.PHANTOM_KEY)

        # Invert current flag
        currently = self.view.settings().get(SETTING_SHOW_BLAME_INLINE, True)
        self.view.settings().set(SETTING_SHOW_BLAME_INLINE, not currently)


class BlameShowAllCommand(BasePlugin):
    PHANTOM_KEY = 'git-blame-all'

    def __init__(self, view):
        super().__init__(view)
        self.phantom_set = sublime.PhantomSet(self.view, self.PHANTOM_KEY)

    # The fixed length for author names
    NAME_LENGTH = 10

    def run(self, edit):
        if self.view.is_dirty():
            sublime.status_message("The file needs to be saved for git blame.")
            return

        self.view.erase_phantoms(self.PHANTOM_KEY)
        phantoms = []

        # If they are currently shown, toggle them off and return.
        if self.view.settings().get(SETTING_PHANTOM_ALL_DISPLAYED, False):
            self.phantom_set.update(phantoms)
            self.view.settings().set(SETTING_PHANTOM_ALL_DISPLAYED, False)
            return

        blame_lines = get_blame_lines(self.view.file_name())

        if not blame_lines:
            return

        for l in blame_lines:
            parsed = parse_blame(l)
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


class BlameEraseAllCommand(BasePlugin):

    def run(self, edit):
        '''Erases the blame results.
        '''
        sublime.status_message("The git blame result is cleared.")
        self.view.erase_phantoms(PHANTOM_KEY_ALL)


class BlameEraseAllListener(BasePlugin):

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


class InsertCommitDescriptionCommand(BasePlugin):

    def run(self, edit, desc, scratch_view_name):
        view = self.view
        view.set_scratch(True)
        view.set_syntax_file('Packages/Diff/Diff.sublime-syntax')
        view.insert(edit, 0, desc)
        view.set_name(scratch_view_name)
