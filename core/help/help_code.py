from talon import actions, Module, Context, registry

from dataclasses import dataclass

from ..gui.gui import open_gui

mod = Module()

@dataclass
class CodeTag:
	name: str
	file_name: str
	lists: list[str] | None
	def __init__(self, name: str, file_name: str="", lists=None):
		self.name = name
		if file_name:
			self.file_name = file_name
		else:
			self.file_name = name.partition(".")[-1]
		self.lists = lists

tags = [
	CodeTag("user.code_comment_line"),
	CodeTag("user.code_keywords", lists=["user.code_keyword", "user.code_keyword_unprefixed"]),
	CodeTag("user.code_functions", lists=["user.code_function_modifier"]),
	CodeTag("user.code_comment_block"),
	CodeTag("user.code_object_oriented", lists=["user.code_common_method"]),
	CodeTag("user.code_data_null"),
	CodeTag("user.code_imperative"),
	CodeTag("user.code_libraries", lists=["user.code_libraries"]),
	CodeTag("user.code_comment_documentation"),
	CodeTag("user.code_data_bool"),
	CodeTag("user.code_functions_common", lists=["user.code_common_function"]),
]

# detected_tags = []
# for tag in registry.tags:
# 	if tag.startswith("user.code_"):
# 		detected_tags.append(tag)
# actions.insert(detected_tags)

def language_has_operators():
	try:
		actions.user.code_get_operators()
		return True
	# This exception will get raised if there is no operators object defined in the active context
	except NotImplementedError:
		return False

@open_gui(refresh_period="500ms")
async def gui_code(ui, ui_wrapper):
	language = actions.code.language()
	title = "Help Code"
	if language:
		subtitle = f"Active Programming Language: {language}"
	else:
		subtitle = "There is no active programming language"
	ui_wrapper.title(title, subtitle)
	if language:
		if ui_wrapper.button("help snip"):
			pass
		if language_has_operators():
			if ui_wrapper.button("help operators"):
				pass
		for tag in tags:
			if True:
				ui.strong(f"tag: {tag.name}")
				if ui_wrapper.button(f"See Commands"):
					pass
				if tag.lists:
					if len(tag.lists) > 1:
						list_section_title = "Lists: "
					else:
						list_section_title = "List: "
					async with ui.horizontal_wrapped():
						ui.strong(list_section_title)
						for l in tag.lists:
							if ui_wrapper.button(l):
								pass
				ui.separator()
				ui_wrapper.spacing()
	if ui_wrapper.button("help close"):
		gui_code.hide()

	
					
@mod.action_class
class Actions:
	def help_code():
		"""Show help for the active programming language"""
		gui_code.show()

	