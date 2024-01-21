from __future__ import annotations

from abc import abstractmethod
from sublime import Region, View
from sublime_plugin import TextCommand
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sublime import Point

__all__ = ["MoveByParagraphCommand"]


class AbstractParagraphFinder:
    def __init__(
        self,
        view: View,
        ignore_blank_lines: bool,
        stop_at_paragraph_begin: bool,
        stop_at_paragraph_end: bool,
    ):
        self.view = view
        self.ignore_blank_lines = ignore_blank_lines
        self.stop_at_paragraph_begin = stop_at_paragraph_begin
        self.stop_at_paragraph_end = stop_at_paragraph_end

    @abstractmethod
    def find(self) -> Point:
        raise NotImplemented

    def _line_begins_paragraph(self, line: Region, line_above: Region) -> bool:
        a = self._substr(line)
        b = self._substr(line_above)
        return bool(a and not b)

    def _line_ends_paragraph(self, line: Region, line_below: Region) -> bool:
        a = self._substr(line)
        b = self._substr(line_below)
        return bool(a and not b)

    def _substr(self, line: Region) -> str:
        s = self.view.substr(line)
        if self.ignore_blank_lines:
            return s.strip()
        return s


class ForwardParagraphFinder(AbstractParagraphFinder):
    def find(self, start) -> Point:
        size = self.view.size()
        r = Region(start, size)

        # Obtain the lines that intersect the region
        lines = self.view.lines(r)

        for n, line in enumerate(lines[:-1]):
            if self.stop_at_paragraph_begin and self._line_begins_paragraph(
                lines[n + 1], line
            ):
                return lines[n + 1].a

            if (
                line.b != start
                and self.stop_at_paragraph_end
                and self._line_ends_paragraph(line, lines[n + 1])
            ):
                return line.b

        # Check if the last line is empty or not
        # If it is empty, make sure we jump to the end of the file
        # If it is not empty, jump to the end of the line
        if self._substr(lines[-1]) == "":
            return size

        end = lines[-1].b

        # If the file ends with a single newline, it will be stuck
        # before this newline character unless we do this
        if end == start:
            return end + 1

        return end


class BackwardParagraphFinder(AbstractParagraphFinder):
    def find(self, start) -> Point:
        r = Region(0, start)

        # Obtain the lines that intersect the region
        lines = self.view.lines(r)
        lines.reverse()

        for n, line in enumerate(lines[:-1]):
            if self.stop_at_paragraph_begin and self._line_begins_paragraph(
                line, lines[n + 1]
            ):
                return line.a

            if self.stop_at_paragraph_end and self._line_ends_paragraph(
                lines[n + 1], line
            ):
                return lines[n + 1].b

        return lines[-1].a


class MoveByParagraphCommand(TextCommand):
    def run(
        self,
        _,
        extend=False,
        forward=False,
        ignore_blank_lines=True,
        stop_at_paragraph_begin=True,
        stop_at_paragraph_end=False,
    ):
        """
        The sel will move to beginning of a non-empty line that succeeds
        an empty one.  Selection is supported when "extend" is True.
        """
        if not stop_at_paragraph_begin and not stop_at_paragraph_end:
            stop_at_paragraph_begin = True

        finder_cls = ForwardParagraphFinder if forward else BackwardParagraphFinder
        finder = finder_cls(
            self.view,
            ignore_blank_lines,
            stop_at_paragraph_begin,
            stop_at_paragraph_end,
        )

        sels = tuple(self.view.sel())
        self.view.sel().clear()
        for sel in sels:
            pt = finder.find(sel.b)
            if extend:
                self.view.sel().add(Region(sel.a, pt))
            else:
                self.view.sel().add(pt)

        self.view.show(self.view.sel()[0])
