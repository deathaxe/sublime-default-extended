from __future__ import annotations

import bisect
import os
import re
import sublime
import sublime_plugin

__all__ = [
    "FindresultsGotoFile",
    "FindresultsGotoMatch",
    "FindresultsOpenFileCommand",
    "FindresultsListener",
]


class FindresultsGoto(sublime_plugin.TextCommand):
    def __init__(self, view):
        super().__init__(view)
        self.beg = []
        self.end = []
        self.revision = -1

    def run(self, _, forward: bool = True):
        sel = self.view.sel()
        try:
            pt = sel[0].b
        except Exception:
            pt = 0

        revision = self.view.change_count()
        if self.revision != revision:
            self.revision = revision
            regs = self.get_matches()
            if regs:
                self.beg = [reg.a for reg in regs]
                self.end = [reg.b for reg in regs]
            else:
                self.beg = []
                self.end = []

        if forward:
            idx = bisect.bisect_right(self.beg, pt)
            if idx >= len(self.beg):
                idx = 0
        else:
            idx = bisect.bisect_left(self.end, pt) - 1
            if idx < 0:
                idx = len(self.beg)

        m = sublime.Region(self.beg[idx], self.end[idx])
        sel.clear()
        sel.add(m)
        self.view.show(m)

    def get_matches(self): ...


class FindresultsGotoFile(FindresultsGoto):
    def get_matches(self):
        return self.view.find_by_selector("entity.name.filename.find-in-files")


class FindresultsGotoMatch(FindresultsGoto):
    def get_matches(self):
        return self.view.get_regions("match")


class FindresultsOpenFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for sel in view.sel():
            line_no = self.get_line_no(sel)
            file_name = self.get_file(sel)
            if line_no and file_name:
                file_loc = "%s:%s" % (file_name, line_no)
                view.window().open_file(file_loc, sublime.ENCODED_POSITION)
            elif file_name:
                view.window().open_file(file_name)

    def get_line_no(self, sel):
        view = self.view
        line_text = view.substr(view.line(sel))
        match = re.match(r"\s*(\d+).+", line_text)
        if match:
            return match.group(1)
        return None

    def get_file(self, sel):
        view = self.view
        line = view.line(sel)
        while line.begin() > 0:
            line_text = view.substr(line)
            match = re.match(r"(.+):$", line_text)
            if match:
                if os.path.exists(match.group(1)):
                    return match.group(1)
            line = view.line(line.begin() - 1)
        return None


class FindresultsListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        if view.name() == "Find Results":
            view.set_read_only(True)
