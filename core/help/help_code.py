from talon import actions, Module, Context, registry

from dataclasses import dataclass


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
	CodeTag("user.code_keywords", lists=["user.code_keyword"]),
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

