[![GitHub contributors](https://img.shields.io/github/contributors/psykzz/st3-gitblame.svg)](https://github.com/psykzz/st3-gitblame/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/psykzz/st3-gitblame.svg)](https://github.com/psykzz/st3-gitblame/issues)
[![CircleCI](https://circleci.com/gh/psykzz/st3-gitblame.svg?style=svg)](https://circleci.com/gh/psykzz/st3-gitblame)


# Git blame - Sublime text 3 plugin
Sublime text 3 - Git blame the line

Small plugin to parse git blame and add a view to show the user and datetime of the blame. You can click the sha to copy it or click the ✖ to close. Also, this package provides a command to see all the blame result of a file.

View on [packagecontrol.io](https://packagecontrol.io/packages/Git%20blame)


## Usage

### Checking the results of `git blame` for selected lines

 > CTRL + ALT + B (Q on linux)

 > Right click > Git blame

### Checking the result of `git blame` for the whole file

To show the `git blame` result: Open the command pallette and select `Git Blame Show All`.

To erase the `git blame` result: Open the command pallette and select `Git Blame Erase All`. Or, you can click the ✖ icon to erase it. Also, the result is automatically erased when you start to modify the file.

## Example

<img width="645" alt="screen shot 2017-07-20 at 11 12 51" src="https://user-images.githubusercontent.com/2543659/28410198-331b1ec8-6d3d-11e7-9ac1-57d43fb6ab60.png">
<img width="672" alt="screen shot 2017-07-20 at 11 13 05" src="https://user-images.githubusercontent.com/2543659/28410200-33312740-6d3d-11e7-8b1e-f46ae7b6925b.png">
<img width="660" alt="screen shot 2017-07-20 at 11 13 20" src="https://user-images.githubusercontent.com/2543659/28410201-3336ad3c-6d3d-11e7-974c-fa5a1f89ea2b.png">
<img width="663" alt="screen shot 2017-07-20 at 11 13 29" src="https://user-images.githubusercontent.com/2543659/28410203-3358c444-6d3d-11e7-980d-e4b49958eb9b.png">
<img width="667" alt="screen shot 2017-07-20 at 11 13 38" src="https://user-images.githubusercontent.com/2543659/28410202-333ccc62-6d3d-11e7-8d7f-ff88067f3cb1.png">
