from talon import Module, Context

import egui
from talon.egui import Window
import skia

from dataclasses import dataclass
from typing import Callable

@dataclass
class Page:
	ui: Callable[[egui.ui], None]
	title: str



class CommandMenu:
	def __init__(self):
		self.window = Window()
		self.window.draggable = True
		self.window.decorated = False
		self.current_page = None
		self.window.rect = skia.Rect(x=10, y=20, width=800, height=800)
		self.window.set_content(self.ui)
		self.pages = []

	async def ui(self, ui: egui.ui) -> None:
		if self.current_page is None:
			ui.strong("What do you want to do?")
			ui.separator()
			for i, page in enumerate(self.pages):
				if ui.button(page.title).clicked():
					self.current_page = i
		else:
			page = self.pages[self.current_page]
			await page.ui()
		if ui.button("Command menu close").clicked():
			self.hide()

	def show(self) -> None:
		self.window.show()

	def hide(self) -> None:
		self.window.hide()

command_menu = CommandMenu()
command_menu.show()

mod = Module()
@mod.action_class
class Actions:
	pass