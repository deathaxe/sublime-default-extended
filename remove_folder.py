from __future__ import annotations

from os.path import basename

import sublime
import sublime_plugin

__all__ = ["PromptRemoveFolderCommand"]

KIND_FOLDER = [sublime.KindId.COLOR_YELLOWISH, "📁", "Folder"]


def project_folders(project):
    return (project or {}).get("folders", [])


def display_name(folder):
    return folder.get("name") or basename(folder["path"])


class DirsInputHandler(sublime_plugin.ListInputHandler):
    __slots__ = ["folders"]

    def __init__(self, folders):
        super().__init__()
        self.folders = folders

    def name(self):
        return "dirs"

    def placeholder(self):
        return "Folder Name"

    def list_items(self):
        return [
            sublime.ListInputItem(
                text=display_name(folder),
                annotation=folder["path"],
                value=folder["path"],
                kind=KIND_FOLDER
            )
            for folder in self.folders
        ]


class PromptRemoveFolderCommand(sublime_plugin.WindowCommand):
    """
    This class implements the `prompt_remove_folder` command.

    It is equivalent to built-in `remove_folder` command, but provides
    an ListInputHandler to choose folder to delete, if `dirs` is invalid
    so it can be used to provide a command palette entry to remove folders
    from sidebar.
    """

    def is_enabled(self, dirs=None):
        return bool(project_folders(self.window.project_data()))

    def is_visible(self, dirs=None):
        return self.is_enabled(dirs)

    def input(self, args):
        if not args.get("dirs"):
            folders = project_folders(self.window.project_data())
            if folders:
                return DirsInputHandler(folders)

        return None

    def input_description(self):
        return "Remove:"

    def run(self, dirs=[]):
        project = self.window.project_data()
        if not project or not isinstance(project, dict):
            return

        if not dirs:
            return

        if isinstance(dirs, str):
            dirs = [dirs]
        elif not isinstance(dirs, list):
            return

        project["folders"] = list(
            filter(lambda folder: folder["path"] not in dirs, project_folders(project))
        )

        self.window.set_project_data(project)
