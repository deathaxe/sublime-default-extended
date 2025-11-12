import sublime
import sublime_plugin


class SingleLastSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sels = view.sel()
        if not sels:
            return

        # Always take the last selection
        last = sels[-1]
        view.sel().clear()
        view.sel().add(last)
        view.show(last)
