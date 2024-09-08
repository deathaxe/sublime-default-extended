from __future__ import annotations

import re
import os
import sublime
import sublime_plugin

from urllib.parse import unquote

DEBUG = False

# creating


class NewScratchFileCommand(sublime_plugin.WindowCommand):
    """
    This class describes a `new_scratch_file` command.

    The command creates a new view and marks it as "scratch",
    so it can be closed without prompting for saving.
    """

    def run(self):
        view = self.window.new_file()
        if view:
            view.set_scratch(True)


class SyntaxSelectorListInputHandler(sublime_plugin.ListInputHandler):
    """
    This class describes a syntax selector list input handler.

    Lists all available syntaxes in command palette.
    """

    def __init__(self, args={}):
        self.args = args

    def name(self):
        return "syntax"

    def placeholder(self):
        return "Select Syntax"

    def preview(self, syntax):
        return sublime.Html(f"<strong>Syntax Path:</strong> <small>{syntax}</small>")

    def list_items(self):
        return [
            sublime.ListInputItem(
                syntax.name,
                syntax.path,
                details=f'Provided by package: <b><u>{syntax.path.split("/")[1]}</u></b>',
                annotation=syntax.scope,
            )
            for syntax in sublime.list_syntaxes()
            if syntax.hidden is False
        ]


class NewFileWithSyntaxCommand(sublime_plugin.WindowCommand):
    """
    This class describes a `new_file_with_syntax` command.

    The command displays a ``ListInputHandler`` to select a syntax
    to assign to newly created view.
    """

    def run(self, syntax):
        self.window.new_file(syntax=syntax)

    def input(self, args):
        if "syntax" not in args:
            return SyntaxSelectorListInputHandler(args)
        return None

    def input_description(self):
        return "Syntax"


class CloneFileToNewGroupCommand(sublime_plugin.WindowCommand):
    """
    This class describes a `clone_file_to_new_group` command.
    """

    def run(self):
        window = self.window

        src_group = window.active_group()
        dst_group = int(src_group == 0)

        src_view = window.active_view_in_group(src_group)
        if not src_view:
            return

        if window.num_groups() < 2:
            window.run_command("clone_file")
            window.run_command("new_pane", {"move": True})

        else:
            # Check if a copy already exists in 'dst_group' and just
            # focus on it if so
            src_file = src_view.file_name()
            for view in window.views_in_group(dst_group):
                if view.file_name() == src_file:
                    window.focus_view(view)
                    return

            # No existing views found - make a new one
            window.run_command("clone_file")
            window.run_command("move_to_group", {"group": dst_group})

        dst_view = window.active_view_in_group(dst_group)
        if not dst_view:
            return

        dst_view.set_viewport_position(src_view.viewport_position(), False)
        dst_view.sel().clear()
        dst_view.sel().add_all(src_view.sel())


class OpenFileFromUrlCommand(sublime_plugin.WindowCommand):
    R"""
    This class describes an open file from url command.

    It is used to open files via protocol interface.

    [HKEY_CLASSES_ROOT\subl]
    "URL Protocol"=""
    [HKEY_CLASSES_ROOT\subl\shell\open\command]
    @="\"sublime_text.exe\" --command \"open_file_from_url {\\\"url\\\": \\\"%1\\\"}\""

    ; pretend we are vscode

    [HKEY_CLASSES_ROOT\vscode]
    "URL Protocol"=""
    [HKEY_CLASSES_ROOT\vscode\shell\open\command]
    @="\"sublime_text.exe\" --command \"open_file_from_url {\\\"url\\\": \\\"%1\\\"}\""

    """
    def run(self, url):
        url = unquote(re.sub(r"^(vscode|subl):(//)?((file|open)/)?", "", url))
        self.window.open_file(url, sublime.ENCODED_POSITION)

# saving


class CreatePathListener(sublime_plugin.EventListener):
    """
    This class describes a create path listener.

    It makes sure to create folders on demand, before saving a file.

    Without this listener, ST fails saving an open view whose file
    and containing folder was deleted externally. Instead it prompts for saving
    beginning in user's home directory or ST's installation directory.
    """

    def on_pre_save(self, view):
        os.makedirs(os.path.dirname(view.file_name()), exist_ok=True)


class SaveAllExistingCommand(sublime_plugin.WindowCommand):
    """
    This class describes a `save_all_existing` command.

    The command only saves views, which are associated with files on disk.
    Any new or scratch view, which has not yet been saved to disk, is ignored.
    """

    def run(self):
        for view in self.window.views():
            if view.file_name():
                view.run_command("save", {"async": True})


# closing

def find_clone(view: sublime.View) -> sublime.View | None:
    w = view.window()
    if w is not None:
        bid = view.buffer_id()
        vid = view.id()

        for v in w.views():
            if bid == v.buffer_id() and vid != v.id():
                return v

    return None


class CloseImmediatelyCommand(sublime_plugin.WindowCommand):
    def run(self, save=True):
        view = self.window.active_view()
        if view:
            is_scratch_clone = False
            clone = find_clone(view)
            if clone:
                if DEBUG:
                    print("Close clone")
                is_scratch_clone = clone.is_scratch()
                view.set_scratch(True)

            else:
                fname = view.file_name()
                if not save or not fname or not os.path.exists(fname):
                    # close immediatly, if file no longer exists
                    view.set_scratch(True)
                    if DEBUG:
                        print("Close deleted file")

                elif view.is_dirty():
                    # save file, before closing
                    if DEBUG:
                        print("Save and close file")
                    view.run_command("save")

            view.close()

            if clone:
                # restore scratch state of clones
                view.set_scratch(is_scratch_clone)

            return

        sheet = self.window.active_sheet()
        if sheet:
            sheet.close()
