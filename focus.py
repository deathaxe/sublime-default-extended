from __future__ import annotations

import sublime_plugin


class FocusActivePanelCommand(sublime_plugin.WindowCommand):
    """
    If there is a panel active, focus it.
    """
    def run(self):
        current = self.window.active_panel()
        if current:
            if current.startswith('output.'):
                current = current[7:]

            view = self.window.find_output_panel(current)
            if view:
                self.window.focus_view(view)


class FocusActiveSheetCommand(sublime_plugin.WindowCommand):
    def run(self):
        active_sheet = self.window.active_sheet()
        if active_sheet:
            self.window.focus_sheet(active_sheet)
