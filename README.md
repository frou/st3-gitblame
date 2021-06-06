[![GitHub release](https://img.shields.io/github/release/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/releases)
[![GitHub contributors](https://img.shields.io/github/contributors/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/issues)

# Git blame - Package for Sublime Text

This package enables you to query Git "blame" information for files while you are viewing/editing them in Sublime Text.

Blame information tells you who last edited a line, when they did it, and which commit they did it in. You can then choose to show that commit in full including its commit message and diff.

For this package to work, you must already have the `git` command-line tool installed, and be viewing/editing a file that is part of a Git repository on your hard drive.

[View on the Package Control website](https://packagecontrol.io/packages/Git%20blame)

This package was originally created by [@psykzz](https://github.com/psykzz) and is now maintained by [@frou](https://github.com/frou)

## How to use

Place the text cursor on the line you are interested in, then press <kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>B</kbd> (Mac/Windows) or <kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>Q</kbd> (Linux).

(Instead of pressing the keyboard shortcut, you can alternatively right click and select *Git Blame* from the context menu)

The blame information will appear:

![Screenshot](https://raw.githubusercontent.com/frou/st3-gitblame/master/docs/screenshot-blame.png)

If you want, you can then click `[Show]` to show the commit in full:

![Screenshot](https://raw.githubusercontent.com/frou/st3-gitblame/master/docs/screenshot-blame-show.png)

...or click `[Copy]` to copy the Commit ID (aka SHA) to your clipboard.

If the latest blame information was not as illuminating as you hoped for, click the `[Prev]` to step back through multiple previous commits that affected the line.

To close the blame information, click the `×` icon, or press the keyboard shortcut again while the text cursor is still on the same line.

## Advanced use

In combination with Sublime Text's *Multiple Selection* feature, you can query blame information for more than one line simultaneously by first placing a text cursor on each line you are interested in, and then running as described above.

You can also query blame information for every line in the entire file simultaneously by pressing <kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>Shift</kbd><kbd>B</kbd> (Mac/Windows) or <kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>C</kbd> (Linux). Doing this shows blame information in a different style (it's located to the left of the content, and more compact, but with fewer features):

![Screenshot](https://raw.githubusercontent.com/frou/st3-gitblame/master/docs/screenshot-blameall.png)

To close all of them, click the `×` icon on any one of them, or press the keyboard shortcut again.

As well as via keyboard shortcuts, this package's commands are also made available in the *Command Palette*. Type "Git Blame" into it to find them:

<!--
@todo Add a Development section to the README with tips for contributors
@body Because of the layout of the package (single "plugin", `boot.py`, and the result of the code in `src/`) it's recommended to use https://packagecontrol.io/packages/AutomaticPackageReloader so that changes you make during development get picked up without needing to restart ST.
@body Try to format the Python code using https://github.com/psf/black.
@body Be mindful of ST API versions https://www.sublimetext.com/docs/api_reference.html. We support ST3 (build 3211+) for now, but may go ST4 exclusive in the future.
-->

![Screenshot](https://raw.githubusercontent.com/frou/st3-gitblame/master/docs/screenshot-palette.png)
