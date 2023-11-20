import sublime


def pkg_settings():
    # NOTE: The sublime.load_settings(...) call has to be deferred to this function,
    # rather than just being called immediately and assigning a module-level variable,
    # because of: https://www.sublimetext.com/docs/3/api_reference.html#plugin_lifecycle
    return sublime.load_settings("Git blame.sublime-settings")


PKG_SETTINGS_KEY_CUSTOMBLAMEFLAGS = "custom_blame_flags"

PKG_SETTINGS_KEY_INLINE_BLAME_ENABLED = "inline_blame_enabled"
PKG_SETTINGS_KEY_INLINE_BLAME_DELAY = "inline_blame_delay"

PKG_SETTINGS_BLAME_ALL_MESSAGE_MAX_LEN = "blame_all_message_max_len"
PKG_SETTINGS_BLAME_ALL_DISPLAY_AUTHOR = "blame_all_display_author"
PKG_SETTINGS_BLAME_ALL_DISPLAY_DATE = "blame_all_display_date"
PKG_SETTINGS_BLAME_ALL_DISPLAY_TIME = "blame_all_display_time"
