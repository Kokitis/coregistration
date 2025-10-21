import sys
from pathlib import Path
from typing import *
from PySide6 import QtWidgets
from coregistration.guiqt import qtimage
from coregistration.imagemanager import ImageManager
from coregistration import resources
import pandas
from loguru import logger
from pprint import pprint
from dataclasses import dataclass
import pyqtgraph as pg
import json
PointType = Tuple[float, float]

pg.setConfigOption('leftButtonPan', False)


class MainGui(QtWidgets.QWidget):
	def __init__(self, window: QtWidgets.QMainWindow, path: Path, folder_output: Path = None):
		super().__init__()
		self.folder_output = folder_output if folder_output else Path(__file__).parent
		self.window = window
		self.centralwidget = QtWidgets.QWidget(parent = self.window)
		self.application_size = (1920, 1080)
		# self.resize(self.application_size[0], self.application_size[1])

		self.manager = ImageManager(path)

		self.button_undo_reference = QtWidgets.QPushButton(parent = self.centralwidget)
		self.button_undo_reference.setText("Undo Top")
		self.button_undo_query = QtWidgets.QPushButton("Undo bottom", parent = self.centralwidget)

		self.button_next = QtWidgets.QPushButton("Next", parent = self.centralwidget)
		self.button_export = QtWidgets.QPushButton("Export", parent = self.centralwidget)
		self.label_index = QtWidgets.QLabel("", parent = self.centralwidget)

		plot_size = (self.application_size[0], (self.application_size[1] - 100) // 2)
		self.image_widget_reference = qtimage.QtImage(plot_size, parent = self.centralwidget)
		self.image_widget_query = qtimage.QtImage(plot_size, parent = self.centralwidget)
		self._setup_geometry()
		self._setup_connections()
		self.window.setCentralWidget(self.centralwidget)

		self.load_group()

	def _setup_connections(self):
		self.button_undo_reference.clicked.connect(self.image_widget_reference.remove_last_point)
		self.button_undo_query.clicked.connect(self.image_widget_query.remove_last_point)

		self.button_export.clicked.connect(self.export_data)
		self.button_next.clicked.connect(self.load_next_group)

	def _setup_geometry(self):
		self.button_undo_reference.setGeometry(0, 0, 150, 25)
		self.button_undo_query.setGeometry(155, 0, 150, 25)
		self.button_next.setGeometry(310, 0, 150, 25)
		self.button_export.setGeometry(470, 0, 150, 25)
		self.label_index.setGeometry(640, 0, 250, 25)

		self.image_widget_reference.setGeometry(0, 50, self.application_size[0], (self.application_size[1] // 2) - 50)
		self.image_widget_query.setGeometry(0, (self.application_size[1] // 2) + 10, self.application_size[0], self.application_size[1] // 2 - 10)

	def load_next_group(self):
		logger.debug(f"Loading next group...")
		self.manager.modify_index(1)
		self.load_group()

	def load_group(self):
		pair = self.manager.get_group()
		logger.debug(f"Reading images...")
		image_reference = resources.Image(pair.path_reference)
		image_query = resources.Image(pair.path_query)

		channel_reference = image_reference.get_channel("Brightfield")
		channel_query = image_query.get_channel("Brightfield")

		ratio = image_reference.shape[-1] / image_reference.shape[-2]

		maximum_height = (self.application_size[1] - 100) // 2
		maximum_width = int(maximum_height * ratio)

		self.image_widget_reference.set_image(channel_reference)
		self.image_widget_query.set_image(channel_query)

		self.image_widget_reference.setGeometry(0, 50, maximum_width, maximum_height)
		self.image_widget_query.setGeometry(0, (self.application_size[1] // 2) + 10, maximum_width, maximum_height)

		logger.debug(f"Updating labels...")
		index_group = self.manager.index
		total_groups = len(self.manager.groups)

		label_text = f"({index_group} of {total_groups}) {pair.barcode_reference} / {pair.barcode_query}"
		self.label_index.setText(label_text)

	def export_data(self):
		pair = self.manager.get_group()

		coordinates_reference = self.image_widget_reference.points
		coordinates_query = self.image_widget_query.points

		if len(coordinates_reference) != len(coordinates_query):
			message = f"THe imagse do not contain the same number of points! ({len(coordinates_reference)} != {len(coordinates_query)})"
			logger.error(message)
		else:
			result = {
				'barcode:reference':     pair.barcode_reference,
				'barcode:query':         pair.barcode_query,
				'coordinates:reference': coordinates_reference,
				'coordinates:query':     coordinates_query
			}
			result = format_export(
				pair.barcode_reference,
				pair.barcode_query,
				coordinates_reference,
				coordinates_query
			)
			path_output = self.folder_output / f"{pair.barcode_reference}-{pair.barcode_query}.transform.calculated.json"
			path_output.write_text(json.dumps(result))
			logger.debug(f"Saved as {path_output.name}")

def format_export(barcode_reference:str, barcode_query:str, coordinates_reference:List[PointType], coordinates_query:List[PointType]):

	transform_coordinates = list()
	for point_reference, point_query in zip(coordinates_reference, coordinates_query):
		record = {
			'barcode:left': barcode_reference,
			'barcode:right': barcode_query,
			'left:x': point_reference[0],
			'left:y': point_reference[1],
			'right:x': point_query[0],
			'right:y': point_query[1],
		}
		transform_coordinates.append(record)


	record = {
		'barcode:reference': barcode_reference,
		'barcode:query': barcode_query,
		'transform:coordinates': transform_coordinates
	}
	return record
def main():
	path = Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/debug/coregistration.tsv")
	folder_output = Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/debug/")
	app = QtWidgets.QApplication(sys.argv)

	window = QtWidgets.QMainWindow()
	window.resize(1920, 1080)

	ui = MainGui(window, path, folder_output = folder_output)
	window.show()

	sys.exit(app.exec())


if __name__ == "__main__":
	main()
