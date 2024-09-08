import sublime
import sublime_plugin


class VisualMovePageCommand(sublime_plugin.TextCommand):
    """
    This class describes a visual move page command.

    This command moves the caret to center of visible viewport,
    if it is not already within, and starts paging up/down from their.

    ```json
    { "command": "visual_move_page", "args": {"forward": true} }
    { "command": "visual_move_page", "args": {"forward": false} }
    ```

    Pressing pageup/pagedown moves caret up/down by one page, from its current
    position even if it is far way from currently visible viewport, which may
    cause unexpected visual scrolling.
    """
    def run(self, edit, forward=True):
        sels = self.view.sel()
        visible_region = self.view.visible_region()
        if len(sels) == 1 and sels[0] not in visible_region:
            first_row, _ = self.view.rowcol(visible_region.begin())
            last_row, _ = self.view.rowcol(visible_region.end())
            centered_row = int((first_row + last_row) / 2)
            centered_pt = self.view.text_point(centered_row, 0)

            # adjust caret position
            self.view.sel().clear()
            self.view.sel().add(centered_pt)

        # call normal page up/down command
        self.view.run_command("move", {"by": "pages", "forward": forward})
