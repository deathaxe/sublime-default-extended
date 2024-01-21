from __future__ import annotations

import sublime
import sublime_plugin

__all__ = [
    "IncreaseSyntaxFontSizeCommand",
    "DecreaseSyntaxFontSizeCommand"
]


class BaseFontSizeCommand(sublime_plugin.ApplicationCommand):
    def run(self, syntax_only=False):

        settings_file = "Preferences.sublime-settings"
        settings = sublime.load_settings(settings_file)
        current_size = settings.get("font_size", 10)

        window = sublime.active_window()
        if window:
            view = window.active_view()
            if view:
                syntax_settings_file = f"{view.syntax().name}.sublime-settings"
                syntax_settings = sublime.load_settings(syntax_settings_file)
                syntax_size = syntax_settings.get("font_size")
                if syntax_only or syntax_size:
                    settings_file = syntax_settings_file
                    settings = syntax_settings
                    if syntax_size:
                        current_size = syntax_size

        new_size = self.modify(current_size)
        if new_size != current_size:
            settings.set("font_size", new_size)
            sublime.save_settings(settings_file)

    def modify(self, font_size):
        return font_size


class IncreaseSyntaxFontSizeCommand(BaseFontSizeCommand):
    """
    This class describes an increase_syntax_font_size command.

    Arguments:
        syntax_only (bool):
            If `True` font size is always increased via syntax specific settings
            even if no syntax specific `font_size` has been specified before.

            If `False` font size is increased globally via user preferences
            if no syntax specific `font_size` is specified. Per syntax otherwise.
    """

    def modify(self, font_size):
        if font_size >= 36:
            font_size += 4
        elif font_size >= 24:
            font_size += 2
        else:
            font_size += 1

        if font_size > 128:
            font_size = 128

        return font_size


class DecreaseSyntaxFontSizeCommand(BaseFontSizeCommand):
    """
    This class describes an decrease_syntax_font_size command.

    Arguments:
        syntax_only (bool):
            If `True` font size is always decreased via syntax specific settings
            even if no syntax specific `font_size` has been specified before.

            If `False` font size is decreased globally via user preferences
            if no syntax specific `font_size` is specified. Per syntax otherwise.
    """

    def modify(self, font_size):
        if font_size >= 40:
            font_size -= 4
        elif font_size >= 26:
            font_size -= 2
        else:
            font_size -= 1

        if font_size < 8:
            font_size = 8

        return font_size
