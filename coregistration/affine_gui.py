import argparse
import json
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from tkinter import ttk
from typing import *
import sys
import matplotlib
import matplotlib.pyplot as plt
import numpy
from loguru import logger

# from affine.imageio import ImageIOTable
import utilities
from affine import imageio
from affine.imageplot import ImagePlot
from affine.pointmanager import PointManager

pprint('')
matplotlib.use('TkAgg')
plt.style.use('fivethirtyeight')
PointType = Tuple[float, float]


@dataclass
class TableFields:
	id_patient: str = 'patientId'
	id_group: str = 'groupId'
	id_panel: str = 'panelId'
	id_image: str = 'imageId'
	path: str = 'imagePath'


COLUMNS = TableFields()


class GUI:
	def __init__(self, filename: Path, folder_output: Path = None):
		# self.image_type = 'channel'
		if folder_output is None:
			folder_output = Path(__file__).parent / "saved_transforms"
		if not folder_output.exists():
			folder_output.mkdir()
		self.folder_output = folder_output

		# Remove images which have already been registered
		barcodes_to_ignore = self.set_imageio_index()

		self.image_path_field = COLUMNS.path
		self.manager = PointManager()  # barcode_left, barcode_right)
		self.imageio = imageio.ImageIOTable(filename, barcodes_to_ignore)

		self.layout_grid = True

		self.debug: bool = True
		self.application_shape = (1404 // 2, 1872 // 2)
		# self.application_shape = (1872//2, 1404//2)
		logger.debug(f"Application Shape: {self.application_shape}")
		self.panel_dimensions = (450, 350)

		# Create an instance of tkinter frame
		self.root = tk.Tk()
		self.root.title('Affine Registration')

		# Set the geometry
		self.root.geometry(f"{self.application_shape[0] + 100}x{self.application_shape[1] + 100}")
		self.root.columnconfigure(10, weight = 1)
		self.root.rowconfigure(10, weight = 1)

		self.imageplot = ImagePlot(self.root)

		# Keep a reference to the two images
		self._image_resource_left: Optional[utilities.Image] = None
		self._image_resource_right: Optional[utilities.Image] = None

		# Register the axes so that selected points are plotted on the correct image.
		self._register_axes()

		if self.layout_grid:
			self.imageplot.canvas.get_tk_widget().grid(column = 0, row = 2, columnspan = 10, rowspan = 8)
		else:
			self.imageplot.canvas.get_tk_widget().pack(padx = 20, side = tk.TOP, fill = tk.BOTH, expand = False)

		self._update_image_coordinates()
		# self.canvas.mpl_connect('button_press_event', self.manager.add_coordinates)
		self.imageplot.canvas.mpl_connect('button_press_event', self.update)
		self.imageplot.canvas.draw_idle()

		self.setup_interface()
		self._next_group()
		self.root.mainloop()

	def set_imageio_index(self):
		# Removes all image pairs which have aalready been registered.
		saved_transforms = list(self.folder_output.iterdir())

		barcode_pairs = [i.name.split('.')[0].split('-') for i in saved_transforms]
		# The pairs should be a tuple to match the format of imageio.
		return [tuple(i) for i in barcode_pairs]

	def update(self, event):
		self.manager.add_coordinates(event)
		self._update_image_coordinates()

	def _update_image_coordinates(self):
		""" Plot the saved coordinated onto the images."""

		coordinates_left, coordinates_right, coordinates_colors = self.manager.get_points()
		length_left = len(coordinates_left)
		length_right = len(coordinates_right)

		if length_left > 0:
			self.imageplot.scatter(numpy.array(coordinates_left), which = 'left', colors = coordinates_colors)

		if length_right > 0:
			self.imageplot.scatter(numpy.array(coordinates_right), which = 'right', colors = coordinates_colors)

		self.imageplot.canvas.draw_idle()
		self.imageplot.canvas.draw()

	def _register_axes(self):
		# Register the axes so that selected points are plotted on the correct image.
		id_axes_left = id(self.imageplot.canvas_ax_left)
		id_axes_right = id(self.imageplot.canvas_ax_right)
		self.manager.register_axes(id_axes_left, 'left')
		self.manager.register_axes(id_axes_right, 'right')

	def _update_image(self, update_channel: bool = True, update_coordinates: bool = True):

		channel_name = self.combobox_channel.get()
		logger.debug(f"Get channel: {channel_name}")

		# The resources.Image class keep a record of the fliename used to create it.
		# We can use this to get the image labels for now.

		image_id_left = self.manager.barcode_left
		image_id_right = self.manager.barcode_right

		if update_channel:
			image_channel_left = self._image_resource_left.get_channel(channel_name)
			image_channel_right = self._image_resource_right.get_channel(channel_name)

			logger.debug(f"ids: {image_id_left} - {image_id_right}")
			self.image_ax_left = self.imageplot.show_image(image_channel_left, which = 'left', label = image_id_left)
			self.image_ax_right = self.imageplot.show_image(image_channel_right, which = 'right',
				label = image_id_right
			)
			self.imageplot.canvas.draw_idle()

		if update_coordinates:
			self._update_image_coordinates()

	def _next_group(self):

		# Get the next group of images
		# Reset the image plot
		self.imageplot.reset()

		group = self.imageio.get_next_group()
		info_left, info_right = group

		# Reset the point manager and the graphics generator.
		del self.manager
		self.manager = PointManager(info_left[COLUMNS.id_image], info_right[COLUMNS.id_image])

		filename_image_left = info_left[self.image_path_field]
		filename_image_right = info_right[self.image_path_field]

		self._image_resource_left = self.imageio.get_image(filename_image_left)
		self._image_resource_right = self.imageio.get_image(filename_image_right)

		# Need to reset the labels associated with each axis in the PointManager
		self._register_axes()
		# Update the displayed index
		text = f"{self.imageio.index} of {len(self.imageio.group_keys)}"
		self.label_index.configure(text = text)

		# Set the available channels in the combobox
		channel_names_left = set(self._image_resource_left.channels.keys())
		channel_names_right = set(self._image_resource_right.channels.keys())

		available_channels = channel_names_left & channel_names_right
		self.combobox_channel['values'] = sorted(available_channels)
		self.combobox_channel.set("DAPI")

		# Get the selected channel form the images.
		self._update_image()

	def _undo(self):
		""" Undoes the last point added to the images."""
		self.manager.remove_last_point()
		self._update_image_coordinates()

	def save_transform(self):

		barcode_left = self.manager.barcode_left
		barcode_right = self.manager.barcode_right
		prefix = f"{barcode_left}-{barcode_right}"

		filename_input_transform_original = self.folder_output / f"{prefix}.transform.manual.txt"
		filename_output_transform_manual = self.folder_output / f"{prefix}.transform.manual.txt"
		filename_output_transform_calculated = self.folder_output / f"{prefix}.transform.calculated.txt"
		filename_output_transform_calculated_sitk = self.folder_output / f"{prefix}.transform.sitk.txt"
		if filename_output_transform_calculated.exists():
			message = f"This save file already exists: '{filename_output_transform_calculated}'"
			logger.debug(message)
			return None
		# Copy the original transform to the output folder
		if filename_output_transform_calculated.exists():
			logger.debug(f"The file already exists: {filename_output_transform_calculated}")
			filename_output_transform_manual.write_text(filename_input_transform_original.read_text())

		# Save the current transform to the output folder.
		coordinates_left, coordinates_right, coordinates_colors = self.manager.get_points()
		parameters = self.manager.get_current_parameters()

		# unpack the transform so we can generate the sitk-compatible transform file.
		solution = parameters.pop('transform')
		solution.to_sitk(filename_output_transform_calculated_sitk)

		filename_output_transform_calculated.write_text(json.dumps(parameters, indent = 4, sort_keys = True))
		logger.debug(f"Saved!")

	def setup_interface(self):
		self.button_update = tk.Button(self.root, text = "Update", command = lambda: self._update_image())
		self.button_next = tk.Button(self.root, text = "next", command = lambda: self._next_group())
		self.button_save = tk.Button(self.root, text = "save", command = lambda: self.save_transform())
		self.button_undo = tk.Button(self.root, text = "undo", command = lambda: self._undo())

		# Make a combobox to select a specific channel

		self.combobox_channel = ttk.Combobox()

		self.button_show = tk.Button(self.root, text = "show points",
			command = lambda: print(self.manager.get_points())
		)

		self.label_index = tk.Label(self.root, text = "0 of 0")
		# self.label.pack(side = "bottom", fill = "both", expand = "yes")
		if self.layout_grid:
			self.button_update.grid(column = 1, row = 0)
			self.button_next.grid(column = 2, row = 0)
			self.button_save.grid(column = 3, row = 0)
			self.button_show.grid(column = 4, row = 0)
			self.button_undo.grid(column = 5, row = 0)
			self.label_index.grid(column = 6, row = 0)
			self.combobox_channel.grid(column = 7, row = 0)
		else:
			self.button_update.pack()
			self.button_next.pack()
			self.button_save.pack()
			self.button_show.pack()
			self.button_undo.pack()
			self.label_index.pack()
			self.combobox_channel.pack()


def create_parser(args: List[str] = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser()

	parser.add_argument(
		"--table",
		help = "Filename of the input table.",
		type = Path,
		dest = 'filename'
	)

	parser.add_argument(
		"-o", "--output",
		help = "A folder to save the output transform files to.",
		type = Path,
		dest = 'folder_output',
		default = Path(__file__).parent
	)

	return parser.parse_args(args)


def main():
	args = ['-f', '/home/proginoskes/Documents/projects/ynajjar/analysis/coregistration/region_groups.barcodes.updated.tsv']
	args = [
		"--table", Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/debug/coregistration.tsv"),
		"--output", Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/debug")
	]
	parser = create_parser(args)

	GUI(parser.filename, parser.folder_output)



if __name__ == "__main__":
	main()
