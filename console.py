from __future__ import annotations

import sublime
import sublime_plugin


class ClearConsoleCommand(sublime_plugin.WindowCommand):
    def run(self):
        p = sublime.load_settings("Preferences.sublime-settings")
        current = p.get("console_max_history_lines")
        try:
            p.set("console_max_history_lines", 1)
            print("")
        finally:
            p.set("console_max_history_lines", current)
