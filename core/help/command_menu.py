from talon import Module, Context, actions

import egui
from egui import Mutable
from talon.egui import Window
import skia

from dataclasses import dataclass
from typing import Callable

@dataclass
class Page:
	ui: Callable
	title: str

def represent_numbered_argument(ui, description, mutable, minimum=None, maximum=None):
	ui.label(f"({description}): ")
	ui.add(egui.DragValue(mutable))
	value = mutable.get()
	if minimum is not None and value < minimum:
		mutable.set(minimum)
	if maximum is not None and value > maximum:
		mutable.set(maximum)

@dataclass
class Table:
	headers: list[str]
	rows: list[list[str]]

def parse_markdown_columns(line):
	columns = []
	i = 0
	n = len(line)

	while i < n:
		in_backtick = False
		start = i
		# look for the next pipe not inside back ticks
		while i < n:
			if line[i] == '`':
				in_backtick = not in_backtick
			if line[i] == "|" and  not in_backtick:
				column = line[start:i].strip()
				if column:
					columns.append(column)
				i += 1
				break
			i += 1
	return columns

def parse_markdown_table(table):
	"""Convert a string containing a markdown table into a list of headers and rows. When parsing columns, do not consider vertical bar symbols inside backticks to separate columns"""
	if not table.strip():
		raise ValueError("Received empty table")
	lines = [line.strip() for line in table.split("\n") if line.strip()]
	headers = parse_markdown_columns(lines[0])
	if not headers:
		raise ValueError(f"Could not find headers in markdown table {table}")
	rows = [parse_markdown_columns(line) for line in lines[2:]]
	if not rows:
		raise ValueError(f"Could not find rows in markdown table {table}")
	return Table(headers, rows)

async def show_row_with_labels(row, contents) -> None:
	index = row.index()
	for column in contents[index]:
		async with row.col() as cell_ui:
			cell_ui.label(column)


async def draw_table(ui, markdown_table, row_height=None, show_row=None):
	headers = markdown_table.headers
	column_width = ui.available_width()/len(headers)
	table = (
			egui.TableBuilder(ui)
			.cell_layout(egui.Layout.left_to_right(egui.Align.Center).with_main_wrap(True))
			.min_scrolled_height(0.0)
			.max_scroll_height(ui.available_height())
		).column(egui.Column.remainder().at_most(column_width)).column(egui.Column.remainder().resizable(True).at_most(column_width))

	async with table.header(20) as header:
		for h in headers:
			async with header.col() as header_ui:
				header_ui.strong(h)

	table = header.table()
	rows = markdown_table.rows
	if row_height is None:
		row_height = ui.spacing().interact_size.y
	if show_row is None:
		show_row = show_row_with_labels
	async with table.body() as body:
		async for row in body.rows(row_height, len(rows)):
			row.set_overline(True)
			await show_row(row, rows)


class CommandMenu:
	def __init__(self):
		self.window = Window()
		self.window.draggable = True
		self.window.decorated = False
		self.current_page = None
		self.window.rect = skia.Rect(x=10, y=20, width=600, height=600)
		self.window.set_content(self.ui)
		self.pages = [
			Page(self.move_the_mouse_ui, "Move the mouse (voice commands)"),
			Page(None, "Move the mouse (eye tracking)"),
			Page(self.mouse_click_ui, "Click"),
			Page(None, "Scroll the mouse"),
			Page(None, "Press keys"),
			Page(None, "Move the cursor"),
			Page(None, "Type text")
		]
		self.grid_screen_number = Mutable(2)
		self.grid_narrowing_number = Mutable(1)

	async def ui(self, ui):
		if self.current_page is None:
			ui.strong("What do you want to do?")
			ui.separator()
			for i, page in enumerate(self.pages):
				if ui.button(page.title).clicked():
					self.current_page = i
			ui.add_space(10)
		else:
			page = self.pages[self.current_page]
			await page.ui(ui)
			ui.add_space(10)
			if ui.button("command menu").clicked():
				self.current_page = None
		if ui.button("Command menu close").clicked():
			self.hide()

	async def move_the_mouse_ui(self, ui):
		ui.label("The mouse grid lets you move the mouse by dictating numbers. You use one of the below commands to open the grid. This divides the area you made the grid around into 9 numbered rectangles. Picking one of the numbers recreates the grid within that rectangle and moves the mouse to the center of that rectangle")
		ui.add_space(10)
		if ui.button("mouse grid").clicked():
			actions.user.grid_select_screen(1)
			actions.user.grid_activate()
		ui.label("Opens the mouse grid on the main screen")
		if ui.button("grid win").clicked():
			actions.user.grid_place_window()
			actions.user.grid_activate()
		ui.label("Opens the mouse grid around the currently focused window")
		async with ui.horizontal():
			if ui.button("grid screen").clicked():
				screen_number = self.grid_screen_number.get()
				actions.user.grid_select_screen(screen_number)
				actions.user.grid_activate()
			represent_numbered_argument(
				ui,
				"and then you say a screen number",
				self.grid_screen_number,
				1
			)
		ui.label("Opens the mouse grid around the given screen. For instance, saying \"grid screen two\" draws the grid on screen 2.")
		async with ui.horizontal():
			if ui.button("grid").clicked():
				actions.user.grid_activate()
				actions.user.grid_narrow_list([self.grid_narrowing_number.get()])
			represent_numbered_argument(
				ui,
				"and then you say a grid rectangle number",
				self.grid_narrowing_number,
				1,
				9
			)
		ui.label("Opens the grid already inside the given grid rectangle. For instance, saying \"grid 1\" opens the grid inside the first rectangle.")
		ui.add_space(10)
		if ui.button("grid close").clicked():
			actions.user.grid_close()
		ui.label("Closes the mouse grid")

	async def mouse_click_ui(self, ui):
		command_table = parse_markdown_table("""| Command      | Description                             |
| ------------ | --------------------------------------- |
| `touch`      | single click                            |
| `duke`       | double click                            |
| `trip click` | triple click                            |
| `drag`       | hold down the left mouse button         |
| `drag end`   | stop holding down the left mouse button |
| `righty`     | right click                             |""")
		await draw_table(ui, command_table)

	def show(self):
		self.window.show()

	def hide(self):
		self.window.hide()

command_menu = CommandMenu()
command_menu.show()

mod = Module()
@mod.action_class
class Actions:
	pass