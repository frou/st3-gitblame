[![GitHub release](https://img.shields.io/github/release/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/releases)
[![GitHub contributors](https://img.shields.io/github/contributors/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/frou/st3-gitblame.svg)](https://github.com/frou/st3-gitblame/issues)

# Git blame - Package for Sublime Text 3

This package enables you to query Git "blame" information for files while you are viewing/editing them in Sublime Text.

Blame information tells you who last edited a line, when they did it, and which commit they did it in. You can then choose to show that commit in full including its commit message and diff.

For this package to work, you must already have the `git` command-line tool installed, and be viewing/editing a file that is part of a Git repository on your hard drive.

[View on the Package Control website](https://packagecontrol.io/packages/Git%20blame)

This package was originally created by [@psykzz](https://github.com/psykzz) and is now maintained by [@frou](https://github.com/frou)

## How to use

Place the text insertion cursor on the line you are interested in, then press <kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>B</kbd> (Mac/Windows) or <kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>Q</kbd> (Linux). Instead of pressing the keyboard shortcut, you can alternatively right click and select *Git Blame* from the context menu.

![Screenshot](https://raw.githubusercontent.com/frou/st3-gitblame/master/screenshot.png)

The blame information will appear. You can then click `[Show]` to show the commit in full, or `[Copy]` to copy the Commit ID (aka SHA) to your clipboard. Click × or press the keyboard shortcut again to close the blame information.

## Advanced use

In combination with Sublime Text's *Multiple Cursor* feature, you can query blame information for more than one line simultaneously by first placing a cursor on each line you are interested in.

You can also query blame information for every line in the entire file simultaneously by pressing <kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>Shift</kbd><kbd>B</kbd> (Mac/Windows) or <kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>C</kbd> (Linux). Click × or press the keyboard shortcut again to close them.

This package's commands are also made available in the *Command Palette*. Type "Git Blame" into it to find them.
