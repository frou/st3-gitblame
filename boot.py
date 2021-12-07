# Only .py files at the top-level of a Sublime package are considered "plugins".
# Make Sublime aware of our *{Command,Listener,Handler} classes by importing them:
from .src.blame import *  # noqa: F401,F403
from .src.blame_all import *  # noqa: F401,F403
from .src.blame_inline import *  # noqa: F401,F403
from .src.blame_instadiff import *  # noqa: F401,F403


def plugin_loaded():
    pass


def plugin_unloaded():
    pass
