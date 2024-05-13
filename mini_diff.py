import sublime
import sublime_plugin


class ResetMiniDiffCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_reference_document(
            self.view.substr(sublime.Region(0, self.view.size()))
        )


class MiniDiffEventListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        if view.settings().get("reset_mini_diff_on_save", False):
            view.run_command("reset_mini_diff")
