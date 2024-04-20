import sublime
import sublime_plugin


class SwitchPanelInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.initial_panel = owner.window.active_panel()

    def placeholder(self):
        return "Select output panel"

    def list_items(self):
        items = []
        selected_item = -1

        name_map = {
            "exec": "Build Output",
        }

        kind = [sublime.KIND_ID_NAVIGATION, "p", "Output"]

        for idx, panel in enumerate(self.owner.output_panels()):
            if panel == self.initial_panel:
                selected_item = idx

            name = panel[len("output.") :]
            view = self.owner.window.find_output_panel(name)

            items.append(
                sublime.ListInputItem(
                    text=name_map.get(name) or name.replace("_", " ").title(),
                    annotation=view.name() if view else "",
                    value=panel,
                    kind=kind,
                )
            )

        return (items, selected_item)

    def preview(self, text):
        self.owner.window.run_command("show_panel", {"panel": text})

    def cancel(self):
        if self.initial_panel:
            self.owner.window.run_command("show_panel", {"panel": self.initial_panel})
        else:
            self.owner.window.run_command("hide_panel")


class SwitchPanelCommand(sublime_plugin.WindowCommand):
    """
    This class implements the `switch_panel` command.

    It cycles through available output panel in given direction.

    ```json
    { "command": "switch_panel", "forward": true }
    ```

    If called without arguments a list input handler is displayed
    to choose from available output panels.
    """

    def input_description(self):
        return "Switch Panel"

    def input(self, args):
        if not any(p in args for p in ("panel", "forward")):
            return SwitchPanelInputHandler(self)
        return None

    def run(self, forward=None, **kwargs):
        if forward is None:
            return

        panels = tuple(self.output_panels())
        try:
            idx = panels.index(self.window.active_panel())
            panel = panels[((idx + 1) if forward else (idx - 1)) % len(panels)]
        except ValueError as e:
            panel = panels[0]

        if panel:
            self.window.run_command("show_panel", {"panel": panel})

    def output_panels(self):
        for name in self.window.panels():
            panel = self.window.find_output_panel(name[len("output.") :])
            if panel and panel.size():
                yield name
