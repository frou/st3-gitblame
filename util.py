import sublime

import subprocess


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
