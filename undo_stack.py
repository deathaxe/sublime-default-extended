from __future__ import annotations

import sublime
import sublime_plugin


class ClearUndoStackCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view:
            return

        view.clear_undo_stack()
        sublime.status_message("Undo Stack of the current file has been cleared")
