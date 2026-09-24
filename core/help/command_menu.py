from talon import Module, Context, actions

import egui
from talon.egui import Window
import skia

from dataclasses import dataclass
from typing import Callable

@dataclass
class Page:
	ui: Callable
	title: str

async def move_the_mouse_ui(ui: egui.ui) -> None:
	ui.label("The mouse grid lets you move the mouse by dictating numbers. You use one of the below commands to open the grid. This divides the area you made the grid around into 9 rectangles. Picking one of the numbers recreates the grid within that rectangle and moves the mouse to the center of that rectangle")
	ui.add_space(10)
	if ui.button("mouse grid").clicked():
		actions.user.grid_select_screen(1)
		actions.user.grid_activate()
	ui.label("Opens the mouse grid on the main screen")
	if ui.button("grid win").clicked():
		actions.user.grid_place_window()
		actions.user.grid_activate()
	ui.label("Opens the mouse grid around the currently focused window")
	ui.add_space(10)
	if ui.button("grid close").clicked():
		actions.user.grid_close()


class CommandMenu:
	def __init__(self):
		self.window = Window()
		self.window.draggable = True
		self.window.decorated = False
		self.current_page = None
		self.window.rect = skia.Rect(x=10, y=20, width=400, height=600)
		self.window.set_content(self.ui)
		self.pages = [
			Page(move_the_mouse_ui, "Move the mouse (voice commands)"),
			Page(None, "Move the mouse (eye tracking)"),
			Page(None, "Click"),
			Page(None, "Scroll the mouse"),
			Page(None, "Press keys"),
			Page(None, "Move the cursor"),
			Page(None, "Type text")
		]

	async def ui(self, ui: egui.ui) -> None:
		if self.current_page is None:
			ui.strong("What do you want to do?")
			ui.separator()
			for i, page in enumerate(self.pages):
				if ui.button(page.title).clicked():
					self.current_page = i
		else:
			page = self.pages[self.current_page]
			await page.ui(ui)
		ui.add_space(10)
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