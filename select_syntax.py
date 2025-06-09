from __future__ import annotations
from functools import partial
from time import time as now

import sublime
import sublime_plugin

from .debounce_decorator import debounced


class SelectSyntaxCommand(sublime_plugin.TextCommand):
    def run(self, _, syntax: str) -> None:
        self.view.assign_syntax(syntax)

    def input(self, args) -> sublime_plugin.CommandInputHandler | None:
        if "syntax" not in args:
            return SyntaxInputHandler(self.view, args)
        return None

    def input_description(self) -> str:
        return "Syntax"


class SyntaxInputHandler(sublime_plugin.ListInputHandler):
    """
    This class describes a syntax selector list input handler.

    Lists all available syntaxes in command palette.
    """

    def __init__(self, view: sublime.View | None, args: dict = {}):
        self.args = args
        self.view = view
        if view:
            self.initial_syntax = view.syntax().path
        else:
            self.initial_syntax = None

    def name(self) -> str:
        return "syntax"

    def placeholder(self):
        return "Choose a syntax…"

    def cancel(self):
        if self.view and self.initial_syntax:
            self.view.assign_syntax(self.initial_syntax)
            self.view = None

    def preview(self, text: str) -> str | sublime.Html:
        if self.view:
            self.preview_syntax(text)
        return sublime.Html(f"<strong>Syntax Path:</strong> <small>{text}</small>")

    @debounced(100, sync=True)
    def preview_syntax(self, syntax: str) -> None:
        if self.view:
            self.view.assign_syntax(syntax)

    def list_items(self) -> tuple[list[sublime.ListInputItem], int]:
        syntax_list = sorted(
            (syntax for syntax in sublime.list_syntaxes() if not syntax.hidden),
            key=lambda x: x.name,
        )
        current_index = 0
        items = []

        for index, syntax in enumerate(syntax_list):
            if syntax.path == self.initial_syntax:
                current_index = index
            items.append(sublime.ListInputItem(syntax.name, syntax.path, annotation=syntax.scope))

        return items, current_index
