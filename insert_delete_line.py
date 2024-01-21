from __future__ import annotations

import sublime_plugin


class InsertLineBeforeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            line = self.view.rowcol(sel.begin())[0]
            self.view.insert(edit, self.view.text_point(line, 0), "\n")


class DeleteLineBeforeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            line = self.view.rowcol(sel.begin())[0] - 1
            if line >= 0:
                kill = self.view.full_line(self.view.text_point(line, 0))
                self.view.replace(edit, kill, "")
