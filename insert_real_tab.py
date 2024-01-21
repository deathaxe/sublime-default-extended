from __future__ import annotations

import sublime
import sublime_plugin


class InsertRealTabCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit):
        old_value = self.view.settings().get("translate_tabs_to_spaces")
        try:
            self.view.settings().set("translate_tabs_to_spaces", False)

            # ... do something which involves inserting tabs
            self.view.insert(edit, self.view.sel()[0].begin(), "\t")

        finally:
            # assuming setting hasn't been view specific before,
            # rust removing it lets project-specific or global preference
            # to take effect again
            self.view.settings().set("translate_tabs_to_spaces", old_value)
