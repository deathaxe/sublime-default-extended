from __future__ import annotations

import sublime
import sublime_plugin


class LineCountListener(sublime_plugin.EventListener):
    """
    This class describes a line count listener.

    Note: Set ``"show_line_column", "disabled"``
          to disable ST's built-in line/column status
    """

    def on_new(self, view: sublime.View):
        """
        Update status for new view.
        """
        self._update(view)

    def on_load(self, view: sublime.View):
        """
        Update status after loading file.
        """
        self._update(view)

    def on_selection_modified(self, view: sublime.View):
        """
        Update status when caret moves.
        """
        self._update(view)

    def _update(self, view: sublime.View):
        sel = view.sel()
        if not sel:
            view.set_status("zzz_lines", "")
            return

        pt = sel[0].begin()
        row, col = view.rowcol(pt)
        cols = len(view.line(pt))
        lines, _ = view.rowcol(view.size())
        view.set_status("zzz_lines", f"L: {(row + 1)}/{(lines + 1)}, C: {col + 1}/{cols + 1}")
