import sys
from pathlib import Path
from typing import *
from PySide6 import QtWidgets, QtGui, QtCore
from coregistration import resources
import numpy
import pyqtgraph as pg
from loguru import logger

pg.setConfigOption('leftButtonPan', False)
from pprint import pprint

PointType = Tuple[int | float, int | float]

class QtImage(pg.GraphicsLayoutWidget):
	""" example application main window """

	def __init__(self, application_size: PointType = (1920, 1080), parent=None):
		super().__init__(parent = parent)
		self.application_size = application_size
		self.resize(self.application_size[0], self.application_size[1])
		self.show()

		self.series_object = None
		self.points = list()
		self.image = None
		self.plot = self.addPlot()
		self.plot.showAxes(False)  # frame it with a full set of axes
		self.plot.invertY(True)  # vertical axis counts top to bottom

		# signal = pg.SignalProxy(self.plot.scene().sigMouseClicked, rateLimit = 60, slot = self.get_mouse_coordinates)
		self.plot.scene().sigMouseClicked.connect(self.get_mouse_coordinates)


		debug = False
		if debug:
			path = Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/images/merged/images/d10sA2t17.tif")
			image = resources.Image(path)
			channel = image.get_channel("Brightfield")
			self.set_image(channel)
			self.set_points(self.points)

	def get_mouse_coordinates(self, event) -> PointType:
		image_pos = self.image.mapFromScene(event.scenePos())
		x = image_pos.x()
		y = image_pos.y()

		self.points.append((x, y))
		self.set_points(self.points)
		return x, y

	def remove_last_point(self):
		self.points = self.points[:-1]
		self.set_points(self.points)

	def set_image(self, array: numpy.ndarray):
		logger.debug(f"Setting image...")
		self.image = pg.ImageItem(array, axisOrder = 'row-major')
		self.plot.clear()
		self.plot.addItem(self.image)
		self.points = list()

	def set_points(self, points: List[PointType] = None):
		if points is None:
			points = self.points
		if points:
			x, y = zip(*points)
			if self.series_object is None:
				self.series_object = self.plot.plot(
					x, y,
					pen = None,
					marker = 'o',
					symbolSize = 10,
					symbolBrush = 'red'
				)
			else:
				self.series_object.setData(x, y)


def numpy_array_to_qimage(array: numpy.ndarray) -> QtGui.QImage:
	height, width = array.shape
	# Ensure the array is in uint8
	if array.dtype != numpy.uint8:
		array_norm = array / array.max()
		array = (array_norm * 255).astype(numpy.uint8)

	# Create QImage from numpy array
	# Create QImage with Format_Grayscale8
	image = QtGui.QImage(array.data, width, height, width, QtGui.QImage.Format_Grayscale8)

	return image