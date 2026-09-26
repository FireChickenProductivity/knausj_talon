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

	async def ui(self, ui, path):
		ui.strong(f"{self.type_name} ({self.name}): {self.text}")
		description = self.get_description()
		if description:
			ui.label(description)
		rules = compute_relevant_rules_for_text(self.text)
		if rules:
			ui.separator()
			for rule in rules:
				ui.label(rule)
		sub_spoken_forms = compute_spoken_forms(self.text)
		if sub_spoken_forms:
			ui.separator()
			for spoken_form in sub_spoken_forms:
				if ui.button(spoken_form.name).clicked():
					path.append(spoken_form)
		pairs = self.get_key_value_pairs()
		if pairs:
			ui.separator()
			for key, value in pairs:
				ui.label(f"{key}: {value}")

		ui.add_space(10)
		async with ui.horizontal_wrapped():
			if ui.button("close").clicked():
				path.clear()
			if len(path) > 1 and ui.button("go back").clicked():
				path.pop()
			if len(path) > 2 and ui.button("go back to start").clicked():
				while len(path) > 1:
					path.pop()
			
				
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

def compute_spoken_forms(text, exclude_total=True):
	text = text.strip()
	forms = []
	start = None
	for i, c in enumerate(text):
		if exclude_total and i == len(text) - 1 and start == 0:
			return []
		if c in ("{", "<"):
			start = i
		elif c == "}":
			form_text = text[start:i+1]
			list_name = form_text[1:-1]
			form = SpokenForm(
				"list",
				form_text,
				lambda : get_list_description(list_name),
				lambda : get_list_contents(list_name),
				list_name,
			)
			forms.append(form)
			start = None
		elif c == ">":
			form_text = text[start:i+1]
			capture_name = form_text[1:-1]
			form = SpokenForm(
				"capture",
				get_capture_rule(capture_name),
				lambda : get_capture_description(capture_name),
				lambda : [],
				capture_name,
			)
			forms.append(form)
			start = None
	return forms



class ExpansionDemo:
	def __init__(self):
		self.window = Window()
		self.window.toplevel = True
		self.window.draggable = True
		self.window.decorated = False
		self.window.set_content(self.ui)
		self.path = []

	async def ui(self, ui):
		if  not self.path:
			self.hide()
		current = self.path[-1]
		await current.ui(ui, self.path)
			

	def show(self, root):
		self.path = [root]
		self.window.show()

	def hide(self):
		self.window.hide()

demo = ExpansionDemo()
demo.show(compute_spoken_forms("<user.keys>", exclude_total=False)[-1])

mod = Module()
@mod.action_class
class Actions:
	def screenshot_expansion_demo():
		"""Remove before merge"""
		actions.user.samuel_screenshot_around_window(demo.window)