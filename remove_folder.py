from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import sublime
import sublime_plugin

__all__ = ["PromptRemoveFolderCommand"]

KIND_FOLDER = [sublime.KindId.COLOR_YELLOWISH, "📁", "Folder"]

if TYPE_CHECKING:
    from typing import Any


def project_folders(project) -> list[dict[str, Any]]:
    return (project or {}).get("folders", [])


class DirsInputHandler(sublime_plugin.ListInputHandler):
    __slots__ = ["folders"]

    def __init__(self, project_file, folders):
        super().__init__()
        self.project_file = Path(project_file)
        self.folders = folders

    def name(self):
        return "dirs"

    def placeholder(self):
        return "Folder Name"

    def list_items(self):
        items = []
        for folder in self.folders:
            folder_path = folder["path"]
            path = Path(folder_path)
            if not path.is_absolute():
                path = self.project_file.parent / path
            path = path.resolve()
            items.append(
                sublime.ListInputItem(
                    text=folder.get("name") or path.name,
                    annotation=str(path),
                    value=folder_path,
                    kind=KIND_FOLDER
                )
            )

        return items


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
                return DirsInputHandler(self.window.project_file_name(), folders)

        return None

    def input_description(self):
        return "Remove:"

    def run(self, dirs=None):
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
