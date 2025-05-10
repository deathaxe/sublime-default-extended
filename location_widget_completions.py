"""
Auto Completion for Find in Files "Where:" field

Implements:
https://github.com/sublimehq/sublime_text/issues/3620
"""
from __future__ import annotations
from enum import IntEnum
from pathlib import Path

import sublime
import sublime_plugin

__all__ = [
    "FindInFilesCommitLocationCompletionCommand",
    "FindInFilesLocationCompletionListener",
]

IS_WINDOWS = sublime.platform() == "windows"
if IS_WINDOWS:
    from ctypes import windll
    from string import ascii_uppercase

    def iterdrives():
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in ascii_uppercase:
            if bitmask & 1:
                yield letter
            bitmask >>= 1


class LocationCompletionType(IntEnum):
    UNKNOWN = 0
    PATH = 1
    FILE = 2
    VARIABLE = 3


def location_completion(
    trigger: str,
    annotation="",
    completion="",
    type=LocationCompletionType.UNKNOWN,
    kind=sublime.KIND_AMBIGUOUS,
    details="",
) -> sublime.CompletionItem:
    return sublime.CompletionItem(
        trigger,
        annotation,
        sublime.format_command(
            "find_in_files_commit_location_completion",
            {"type": type, "completion": completion or trigger},
        ),
        sublime.COMPLETION_FORMAT_COMMAND,
        kind,
        details,
    )


class FindInFilesLocationCompletionListener(sublime_plugin.EventListener):
    # globally suggested everywhere
    operator_completions: list[sublime.CompletionValue] = [
        sublime.CompletionItem(
            trigger=",",
            kind=(sublime.KIND_ID_KEYWORD, "o", "Separator"),
            details="Separates patterns"
        ),
    ]

    # suggested at beginning of patterns
    variable_completions: list[sublime.CompletionValue] = [
        sublime.CompletionItem(
            trigger="-",
            kind=(sublime.KIND_ID_KEYWORD, "o", "Operator"),
            details="Exclude matching patterns from search"
        ),
        sublime.CompletionItem(
            trigger="//",
            kind=(sublime.KIND_ID_KEYWORD, "o", "Operator"),
            details="Match relative to project folders"
        ),
        sublime.CompletionItem(
            trigger="*/",
            kind=(sublime.KIND_ID_KEYWORD, "o", "Operator"),
            details="Match relative to any folder"
        ),
        location_completion(
            trigger="<current file>",
            type=LocationCompletionType.VARIABLE,
            kind=sublime.KIND_VARIABLE,
            details="Search in active file.",
        ),
        location_completion(
            trigger="<open files>",
            type=LocationCompletionType.VARIABLE,
            kind=sublime.KIND_VARIABLE,
            details="Search in all open files.",
        ),
        location_completion(
            trigger="<open folders>",
            type=LocationCompletionType.VARIABLE,
            kind=sublime.KIND_VARIABLE,
            details="Search in all open folders.",
        ),
        location_completion(
            trigger="<project filters>",
            type=LocationCompletionType.VARIABLE,
            kind=(sublime.KindId.KEYWORD, "f", "filter"),
            details="Apply project specific filter settings.",
        ),
    ]

    def on_query_completions(
        self, view: sublime.View, prefix: str, locations: list[sublime.Point]
    ) -> sublime.CompletionList | None:
        if view.element() != "find_in_files:input:location":
            # not within find in files "Where:" input
            return None
        if view.settings().get("auto_complete_disabled"):
            # auto completions are disabled by configuration
            return None
        if not view.match_selector(0, "source.file-pattern"):
            # completions rely on properly scoped location patterns
            return None

        pt = locations[0]

        completions = self.operator_completions.copy()

        try:
            completions += self.path_completions(view, prefix, pt)
        except OSError:
            pass

        if view.match_selector(max(0, pt - 1), "- meta.path"):
            completions += self.file_completions(view, prefix, pt)
            completions += self.variable_completions

            window = view.window()
            if window:
                active_view = window.active_view()
                if active_view:
                    fname = active_view.file_name()
                    if fname:
                        completions.append(
                            location_completion(
                                trigger="<current folder>",
                                completion=str(Path(fname).parent),
                                type=LocationCompletionType.VARIABLE,
                                kind=sublime.KIND_VARIABLE,
                                details="Search in current folder",
                            )
                        )

        return sublime.CompletionList(
            completions, sublime.AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS
        )

    def file_completions(
        self, view: sublime.View, prefix: str, pt: sublime.Point
    ) -> list[sublime.CompletionValue]:
        completions = []

        # collect file extensions
        window = view.window()
        if window:
            extensions = {"*"}
            for view in window.views():
                fname = view.file_name()
                if fname:
                    _, ext = fname.rsplit(".", 1)
                    if ext:
                        extensions.add(ext)

            for ext in extensions:
                completions.append(
                    location_completion(
                        trigger=f"*.{ext}",
                        type=LocationCompletionType.FILE,
                        kind=(sublime.KindId.TYPE, "e", "extension"),
                        details=f"include <em>{ext}</em> files.",
                    )
                )

        return completions

    def path_completions(
        self, view: sublime.View, prefix: str, pt: sublime.Point
    ) -> list[sublime.CompletionValue]:
        check_pt = max(0, pt - 1)
        selector = "meta.path - punctuation.definition"
        if view.match_selector(check_pt, selector):
            reg = view.expand_to_scope(check_pt, selector)
            if reg:
                reg.b = pt
                path_string = view.substr(reg)
                if path_string.startswith("//"):
                    window = view.window()
                    if not window:
                        return []

                    project_folders = window.folders()
                    if not project_folders:
                        return []

                    parts = path_string[2:].replace("\\", "/").rsplit("/", 1)
                    if len(parts) < 2:
                        folders = [Path(f) for f in project_folders]
                    else:
                        path_string = parts[0]

                        folders = []
                        for root in project_folders:
                            folder = Path(root) / path_string
                            if folder.is_dir():
                                folders.append(folder)

                else:
                    folder = Path(path_string.replace("\\", "/").rsplit("/", 1)[0] + "/")
                    if not folder.is_absolute():
                        # todo handle relative paths which can start everywhere
                        # in the tree of project folders
                        return []

                    folders = [folder]
            else:
                folders = [Path("/")]
        else:
            folders = [Path("/")]

        if IS_WINDOWS and len(folders) == 1 and not folders[0].drive:
            # return drive letter only at beginning of file patterns
            reg = view.expand_to_scope(pt, "meta.file - punctuation.definition")
            if reg and pt - reg.a > 1:
                return []

            # return a list of available drives on Windows OS
            return [
                location_completion(
                    trigger=f"{drive}:",
                    type=LocationCompletionType.PATH,
                    kind=(sublime.KindId.NAMESPACE, "d", "drive"),
                )
                for drive in iterdrives()
            ]

        else:
            # deduplicate folder names
            items = {
                item.name
                for folder in folders
                for item in folder.iterdir()
                if item.is_dir()
            }
            return [
                location_completion(
                    trigger=item,
                    type=LocationCompletionType.PATH,
                    kind=(sublime.KindId.NAMESPACE, "d", "directory"),
                )
                for item in items
            ]


class FindInFilesCommitLocationCompletionCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, type: LocationCompletionType, completion: str):
        sels = self.view.sel()
        if not sels:
            return

        pt = sels[0].b

        if type == LocationCompletionType.FILE:
            self.commit_file(edit, pt, completion)
        elif type == LocationCompletionType.PATH:
            self.commit_path(edit, pt, completion)
        elif type == LocationCompletionType.VARIABLE:
            self.commit_variable(edit, pt, completion)

    def commit_file(self, edit, pt, completion):
        # insert new file filter
        self.view.insert(edit, pt, completion)

    def commit_path(self, edit, pt, completion):
        # trim existing path
        # TODO: keep parts, valid after completion
        reg = self.view.expand_to_scope(
            max(0, pt - 1), "meta.path - punctuation.definition"
        )
        if reg:
            self.view.erase(edit, sublime.Region(pt, reg.b))
            reg.b = pt

        # determine path separator
        if IS_WINDOWS:
            psep = "\\"
            if reg:
                path = self.view.substr(reg)
                # looks like a internal project path
                if "/" in path:
                    psep = "/"
        else:
            psep = "/"

            # prepand /
            if reg is None or reg.a == pt:
                completion = psep + completion

        # insert new path
        self.view.insert(edit, pt, completion + psep)
        # trigger auto completion
        sublime.set_timeout(
            lambda: self.view.run_command("auto_complete", {"mini": True}), 10
        )

    def commit_variable(self, edit, pt, completion):
        # replace existing, possibly incomplete <variable>
        for reg in self.view.find_all(r"<[a-z ]*>?|[a-z ]*?>"):
            if pt in reg:
                # keep leading space
                if self.view.substr(reg.a) == " ":
                    reg.a += 1
                self.view.replace(edit, reg, completion)
                return

        # insert new variable
        self.view.insert(edit, pt, completion)
