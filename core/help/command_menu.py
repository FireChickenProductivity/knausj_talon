from talon import Module, Context, actions, registry, settings

from ..gui.gui import open_gui, UIWrapper, convert_key_value_pairs_to_rows, compute_table_height, PageScroller

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
	contains_navigation_buttons_itself: bool=False

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
				if column.startswith("`") and column.endswith("`") and len(column) > 1:
					column = column[1:-1]
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

async def show_row_with_labels(row, contents):
	index = row.index()
	for column in contents[index]:
		async with row.col() as cell_ui:
			cell_ui.label(column)

async def show_row_with_buttons(row, contents, text_to_button_function):
	index = row.index()
	for column in contents[index]:
		async with row.col() as ui:
			if column in text_to_button_function:
				if ui.button(column).clicked():
					text_to_button_function[column]()
			else:
				ui.label(column)

async def draw_table(ui, markdown_table, row_height=None, show_row=None, auto_size_columns=False, maximum_height=None):
	if maximum_height is None:
		maximum_height = ui.available_height()
	headers = markdown_table.headers
	column_width = ui.available_width()/len(headers)
	table = (
			egui.TableBuilder(ui)
			.cell_layout(egui.Layout.left_to_right(egui.Align.Center).with_main_wrap(True))
			.min_scrolled_height(0.0)
			.max_scroll_height(maximum_height)
			.id_salt(str(markdown_table.rows))
		)
	for i in range(len(headers)):
		if auto_size_columns:
			table = table.column(egui.Column.auto())
		else:
			table = table.column(egui.Column.remainder().at_most(column_width))

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

page_scrollers = {}
for scroller_name in ("arrow", "modifier", "number", "special", "function", "letter", "symbol"):
	page_scrollers[scroller_name] = PageScroller()

async def draw_list(ui, ui_wrapper, name, scroller_name, title):
	selected_list = name
	page_scroller = page_scrollers[scroller_name]

	# clicking the close button forces a refresh even though we are closing this gui.
	# #If we are closing this list, just return
	if not selected_list:
		return

	# Extract description from list declaration, i.e. mod.list(..., desc=...))
	if (desc := registry.decls.lists[selected_list].desc) is not None:
		subtitle = desc
	else:
		subtitle = ""

	title_rich_text = egui.RichText(title).size(ui_wrapper.get_text_size() * 1.5).strong()
	ui.label(title_rich_text)
	if subtitle:
		ui.strong(subtitle)
	ui_wrapper.spacing()


	# setup paging handling
	page_size = settings.get("user.help_max_command_lines_per_page")
	page_scroller.page_size = page_size
	row_size = ui_wrapper.get_label_row_size()
	maximum_height = compute_table_height(
		row_size, ui_wrapper.get_item_spacing(), page_size
	)

	# get the list
	talon_list = actions.user.talon_get_active_registry_list(selected_list)
	rows = convert_key_value_pairs_to_rows(talon_list)

	# show the rows in a table
	if len(rows) > 0:
		max_first_column_length = max(max(len(row[0]) for row in rows) - len("Spoken Form"), 0)
		headers = ["Spoken Form   " + " "*max_first_column_length, "Value"]
		print(name, len(headers[0]))
		await ui_wrapper.draw_table(
			headers,
			rows,
			maximum_height=maximum_height,
			row_height=row_size,
			id_salt=title,
			scroller=page_scroller,
			# temporary measure
			auto_size_columns=True
		)

	ui_wrapper.spacing()

	# show navigation buttons. these are arranged horizontally but will wrap onto more rows if needed
	async with ui.horizontal_wrapped():
		if len(rows) > page_size:
			if ui_wrapper.button(f"{scroller_name} next"):
				page_scroller.page_down()

			if ui_wrapper.button(f"{scroller_name} previous"):
				page_scroller.page_up()
	
	

class CommandMenu:
	def __init__(self):
		self.current_page =  4
		self.pages = [
			Page(self.move_the_mouse_ui, "Move the mouse (voice commands)"),
			Page(self.eye_tracking_ui, "Move the mouse (eye tracking)"),
			Page(self.mouse_click_ui, "Click"),
			Page(self.mouse_scrolling_ui, "Scroll the mouse"),
			Page(self.key_pressing_ui, "Press keys", contains_navigation_buttons_itself=True),
			Page(None, "Move the cursor"),
			Page(None, "Type text")
		]
		self.grid_screen_number = Mutable(2)
		self.grid_narrowing_number = Mutable(1)

	async def ui(self, ui, ui_wrapper):
		show_navigation_buttons_here: bool = True
		if self.current_page is None:
			ui.strong("What do you want to do?")
			ui.separator()
			for i, page in enumerate(self.pages):
				if ui.button(page.title).clicked():
					self.current_page = i
			ui.add_space(10)
		else:
			page = self.pages[self.current_page]
			await page.ui(ui, ui_wrapper)
			show_navigation_buttons_here = not page.contains_navigation_buttons_itself
			ui.add_space(10)
			if show_navigation_buttons_here:
				self.draw_menu_button(ui)
		if show_navigation_buttons_here:
			self.draw_close_menu_button(ui)

	def draw_menu_button(self, ui):
		if ui.button("command menu").clicked():
			self.current_page = None

	def draw_close_menu_button(self, ui):
		if ui.button("Command menu close").clicked():
			self.hide()

	async def move_the_mouse_ui(self, ui):
		ui.label("The mouse grid lets you move the mouse by dictating numbers. You use one of the below commands to open the grid. This divides the area you made the grid around into 9 numbered rectangles. Saying one of the numbers recreates the grid within that rectangle and moves the mouse to the center of that rectangle")
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
		command_table = parse_markdown_table("""| Command	  | Description							 |
| ------------ | --------------------------------------- |
| `touch`	  | single click							|
| `duke`	   | double click							|
| `trip click` | triple click							|
| `drag`	   | hold down the left mouse button		 |
| `drag end`   | stop holding down the left mouse button |
| `righty`	 | right click							 |""")
		await draw_table(ui, command_table)

	async def eye_tracking_ui(self, ui):
		ui.label("See the wiki for instructions on how to set up an eye tracking device.")
		ui.add_space(10)
		ui.label("Use can use the following voice commands to control your eye tracking device.")
		command_table = parse_markdown_table("""| Commands		  | Description						  |
| ----------------- | ------------------------------------ |
| `run calibration` | start Tobii calibration			  |
| `control mouse`   | toggle on/off Tobii moving the mouse |
| `zoom mouse`	  | Toggle Control Mouse (Zoom).		 |
| `control off`	 | Turn the eye tracker off			 |""")
		functions = {
			"run calibration": actions.tracking.calibrate,
			"control mouse": actions.tracking.control_toggle,
			"zoom mouse": actions.tracking.control_zoom_toggle,
			"control off": actions.user.mouse_sleep,
		}
		await draw_table(ui, command_table, show_row=lambda row, contents: show_row_with_buttons(row, contents, functions))
		ui.add_space(10)
		ui.label("When using Zoom, you look at what you want to click on, make a popping noise to zoom in on the current region of the screen, and then fine tune the position before clicking.")
		ui.label("When using Control Mouse, move the cursor with your eyes and fine in your position with your head.")
		ui.add_space(10)
		ui.strong("Notes on Control Mouse")
		ui.label("""The intended use is that you look at the thing you want to click on, then move your head (rotate, tilt, whatever) to put the mouse cursor over the thing, then use some method of clicking (like a voice command or physical button).

Moving your head is an important part of the new Control Mouse - moving your head locks your cursor to the current region until you look to a new part of the screen. This means the cursor will stabilize more when you start moving your head.

The speed at which you move your head has an exponential effect on the speed the mouse moves, so if you move your head very slowly, the mouse will only move a few pixels, but if you move your head very quickly, you can move the mouse by several inches.
""")

	async def mouse_scrolling_ui(self, ui):
		command_table = parse_markdown_table("""| Command		| Description							|
| -------------- | -------------------------------------- |
| `page down`	| press the Page Down key				|
| `page up`	  | press the Page Up key				  |
| `scroll down`  | scroll down							|
| `scroll up`	| scroll up							  |
| `wheel down`   | scroll down with the mouse			 |
| `wheel up`	 | scroll up with the mouse			   |
| `wheel left`   | scroll left with the mouse			 |
| `wheel right`  | scroll right with the mouse			|
| `wheel gaze`   | scroll according to the mouse position |
| `wheel upper`  | continually scroll up with the mouse   |
| `wheel downer` | continually scroll down with the mouse |
| `wheel stop`   | stop scrolling						 |""")
		await draw_table(ui, command_table)

	async def key_pressing_ui(self, ui, ui_wrapper):
		async with ui.with_layout(egui.Layout.top_down(egui.Align.Center)):
			ui_wrapper.title("How to Press Keys")
			ui.strong("Command Mode")
			ui.add_space(5)
			ui.label("You press ordinary keys just by saying the spoken forms for the keys. You can do a keystroke by saying the name of a modifier key or multiple modifier keys followed by a key that is not a modifier. Keys in the lists denoted with a * and the modifier keys can only be used as part of a keystroke including a modifier or by saying \"press\" and then the name of the key.")

			ui.strong("Dictation Mode")
			ui.add_space(5)
			ui.label("In dictation mode, you press keys by saying press and then either a key to press or a keystroke.")
			ui.separator()
			# ui.add_space(10)
			# self.draw_menu_button(ui)
			# self.draw_close_menu_button(ui)
			async with ui.with_layout(egui.Layout.left_to_right(egui.Align.TOP)):
				async with ui.vertical() as vertical_ui:
					await draw_list(vertical_ui, ui_wrapper, "user.modifier_key", "modifier", "Modifier Keys")
					ui.add_space(5)
					await draw_list(vertical_ui, ui_wrapper, "user.arrow_key", "arrow", "Arrow Keys*")
					ui.add_space(5)
					await draw_list(vertical_ui, ui_wrapper, "user.number_key", "number", "Number Keys*")
				ui.separator()
				async with ui.vertical() as vertical_ui:
					await draw_list(vertical_ui, ui_wrapper, "user.special_key", "special", "Special Keys")
					await draw_list(vertical_ui, ui_wrapper, "user.function_key", "function", "Function Keys")
				ui.separator()
				async with ui.vertical() as vertical_ui:
					await draw_list(vertical_ui, ui_wrapper, "user.letter", "letter", "Letter Keys")
				ui.separator()
				async with ui.vertical() as vertical_ui:
					await draw_list(vertical_ui, ui_wrapper, "user.symbol_key", "symbol", "Symbol Keys")


	def show(self):
		# self.current_page = None
		actions.user.show_command_menu()

	def hide(self):
		actions.user.hide_command_menu()

command_menu = CommandMenu()
@open_gui(y=0, width=0.4, height=0.9, refresh_period="500ms")
async def gui(ui, ui_wrapper):
	await command_menu.ui(ui, ui_wrapper)

mod = Module()
@mod.action_class
class Actions:
	def show_command_menu():
		"""Show a menu for seeing how to do basic things using Community"""
		gui.show()

	def hide_command_menu():
		"""Hide the Community command menu"""
		gui.hide()

	def screenshot_command_menu():
		"""Screenshot the current page saving to the clipboard. Depends on Sam's community fork. Remove this before merge"""
		if command_menu:
			actions.user.samuel_screenshot_around_window(command_menu.window)