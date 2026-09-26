from talon import Module, Context, actions

import egui
from egui import Mutable
from talon.egui import Window
import skia

from dataclasses import dataclass
from typing import Callable

def compute_relevant_rules_for_text(text):
	return []

class SpokenForm:
	def __init__(self, type_name, text, get_description, get_key_value_pairs):
		self.type_name = type_name
		self.text = text
		self.get_description = get_description
		self.get_key_value_pairs = get_key_value_pairs

	async def ui(self, ui, path):
		ui.strong(f"{self.type_name}: {self.text}")
		if self.get_description:
			ui.label(self.get_description)
		rules = compute_relevant_rules_for_text(self.text)
		if rules:
			ui.separator()
			for rule in rules:
				ui.label(rule)
		sub_spoken_forms = compute_spoken_forms(self.text)
		if sub_spoken_forms:
			ui.separator()
			for spoken_form in sub_spoken_forms:
				if ui.button(spoken_form.text).clicked():
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
	pass

def get_list_contents(name):
	pass

def compute_spoken_forms(text):
	forms = []
	start = None
	for i, c in enumerate(text):
		if c in ("{", "<"):
			start = i
		elif c == "}":
			form_text = text[start:i+1]
			list_name = text[1:-1]
			form = SpokenForm(
				"list",
				form_text,
				lambda : get_list_description(list_name),
				lambda : get_list_contents(list_name)
			)
			forms.append(form)



class ExpansionDemo:
	def __init__(self):
		self.window = Window()
		self.window.toplevel = True
		self.window.draggable = True
		self.window.decorated = False
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