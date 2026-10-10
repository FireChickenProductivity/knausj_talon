from talon import Module, Context, actions, registry

import egui
from egui import Mutable
from talon.egui import Window
import skia

from dataclasses import dataclass
from typing import Callable

def compute_relevant_rules_for_text(text):
	return []

class SpokenForm:
	def __init__(self, type_name, text, get_description, get_key_value_pairs, name):
		self.type_name = type_name
		self.text = text
		self.get_description = get_description
		self.get_key_value_pairs = get_key_value_pairs
		self.name = name
		self.children = None

	# async def ui(self, ui, path):
	# 	ui.strong(f"{self.type_name} ({self.name}): {self.text}")
	# 	description = self.get_description()
	# 	if description:
	# 		ui.label(description)
	# 	rules = compute_relevant_rules_for_text(self.text)
	# 	if rules:
	# 		ui.separator()
	# 		for rule in rules:
	# 			ui.label(rule)
	# 	sub_spoken_forms = compute_spoken_forms(self.text)
	# 	if sub_spoken_forms:
	# 		ui.separator()
	# 		for spoken_form in sub_spoken_forms:
	# 			if ui.button(spoken_form.name).clicked():
	# 				path.append(spoken_form)
	# 	pairs = self.get_key_value_pairs()
	# 	if pairs:
	# 		ui.separator()
	# 		for key, value in pairs:
	# 			ui.label(f"{key}: {value}")

	# 	ui.add_space(10)
	# 	async with ui.horizontal_wrapped():
	# 		if ui.button("close").clicked():
	# 			path.clear()
	# 		if len(path) > 1 and ui.button("go back").clicked():
	# 			path.pop()
	# 		if len(path) > 2 and ui.button("go back to start").clicked():
	# 			while len(path) > 1:
	# 				path.pop()
			
				
def get_list_description(name):
	return registry.decls.lists[name].desc

def get_list_contents(name):
	try:
		return actions.user.talon_get_active_registry_list(name).items()
	except Exception as ex:
		return []

def get_capture_description(name):
	return registry.decls.captures[name].desc

def get_capture_rule(name):
	capture = registry.captures[name][-1]
	rule = capture.rule
	return rule.rule

def create_list(name, form_text):
	return SpokenForm(
			"list",
			form_text,
			lambda : get_list_description(name),
			lambda : get_list_contents(name),
			name,
		)

def create_capture(name):
	return SpokenForm(
		"capture",
		get_capture_rule(name),
		lambda : get_capture_description(name),
		
		lambda : [],
		name,
	)

def compute_spoken_forms(text, exclude_total=True):
	text = text.strip()
	lists = []
	captures = []
	start = None
	for i, c in enumerate(text):
		if exclude_total and i == len(text) - 1 and start == 0:
			return []
		if c in ("{", "<"):
			start = i
		elif c == "}":
			form_text = text[start:i+1]
			list_name = form_text[1:-1]
			form = create_list(list_name, form_text)
			lists.append(form)
			start = None
		elif c == ">":
			form_text = text[start:i+1]
			capture_name = form_text[1:-1]
			form = create_capture(capture_name)
			captures.append(form)
			start = None
	return lists, captures



class ExpansionDemo:
	def __init__(self):
		self.window = Window()
		self.window.rect = skia.Rect(500, 100, 700, 800)
		self.window.toplevel = True
		self.window.draggable = True
		self.window.decorated = False
		self.window.set_content(self.ui)
		self.root = None

	async def show_expansion(self, ui, encountered=None, root=None, capture: SpokenForm | None=None):
		ui.separator()
		if encountered is None:
			encountered = set()
		if root is None:
			root = self.root
		if capture is None:
			title = f"Expansion Of {root}"
		else:
			title = f"Capture {capture.name}. {capture.get_description()}"
		ui.strong(title)
		if capture:
			ui.label(f"Rule: {capture.text}")
		lists, captures = compute_spoken_forms(root, exclude_total=False)
		encountered.add(root)
		new_captures = []
		async with ui.indent(title):
			async with ui.horizontal_wrapped():
				if lists:
					ui.label("lists: ")
					for l in lists:
						if ui.button(l.name).clicked():
							pass
				if captures:
					ui.label("captures: ")
					for c in captures:
						if c.text not in encountered:
							encountered.add(c.text)
							new_captures.append(c)
						if ui.button(c.name).clicked():
							pass
			for c in new_captures:
				await self.show_expansion(ui, encountered, c.text, c)

	async def ui(self, ui):
		if self.root:
			maximum_height = ui.available_height() - 30
			scroll_area = egui.ScrollArea.vertical().max_height(maximum_height)
			async with scroll_area.show():
				await self.show_expansion(ui) 

		
		
		if ui.button("hide").clicked():
			self.hide()

	def show(self, root):
		self.root = root
		self.window.show()

	def hide(self):
		self.window.hide()

demo = ExpansionDemo()
demo.show("<user.keys>")

mod = Module()
@mod.action_class
class Actions:
	def screenshot_expansion_demo():
		"""Remove before merge"""
		actions.user.samuel_screenshot_around_window(demo.window)

	def hide_expansion_window():
		""""""
		demo.hide()