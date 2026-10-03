from __future__ import annotations

import sublime_plugin


class FocusActivePanelCommand(sublime_plugin.WindowCommand):
    """
    If there is a panel active, focus it.
    """

    def run(self):
        if current := self.window.active_panel():
            if current.startswith("output."):
                current = current[7:]
                if view := self.window.find_output_panel(current):
                    self.window.focus_view(view)
            elif current in ("console", "find", "find_in_files", "replace"):
                self.window.run_command("show_panel", {"panel": current, "toggle": True})


class FocusActiveSheetCommand(sublime_plugin.WindowCommand):
    def run(self):
        if active_sheet := self.window.active_sheet():
            self.window.focus_sheet(active_sheet)
