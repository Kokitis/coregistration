from typing import *

import matplotlib.pyplot as plt
import numpy
import roifile
from loguru import logger
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from vectratools import graphics

ImageSelection = Literal['left', 'right']
ImageFormats = Literal['channel', 'coordinates', 'regions']


class ImagePlot:
	""" Handles the plotting for the gui. Requires a root tkinter application."""

	def __init__(self, root):
		self.root = root

		#self.figure, self.axes = plt.subplots(2, 1, figsize = (7, 10), sharex = True)
		self.figure, self.axes = plt.subplots(2, 1, figsize = (11, 16), sharex = True)
		self.canvas_ax_left, self.canvas_ax_right = self.axes
		self.canvas = FigureCanvasTkAgg(self.figure, self.root)

	def _get_ax(self, which: ImageSelection) -> plt.Axes:
		index = 0 if which == 'left' else 1
		return self.axes[index]

	def reset(self):
		self.canvas_ax_left.cla()
		self.canvas_ax_right.cla()

	def show_image(self, image: numpy.ndarray, which: ImageSelection, label: str = None) -> plt.Axes:
		ax = self._get_ax(which = which)

		# Some of the images are very dark when plotted, so try to brighten them.
		logger.debug(f"{image.min()=}\t{image.max()=}")
		image = (image / image.max())*2
		image = numpy.clip(image, 0, 1)

		image_mean = image.mean()
		image_max = image.max()
		logger.debug(f"{image.shape=}")
		# logger.debug(f"The mean intensity value is {image.mean():.3f} ({image_min}, {image_max})")
		# Brighten images that are too dim.
		if image_max < 1:
			difference = 1 - image_mean
			image = image + difference
			image = numpy.clip(image, 0, 1)
		# logger.debug(f"The adjustment: {image.mean():.3f} ({image_min:.3f}, {image_max:.3f}) (diff = {difference:.3f})")

		ax.imshow(image, cmap = 'gray')
		ax.grid(False)
		ax.xaxis.set_visible(False)
		ax.yaxis.set_visible(False)
		plt.tight_layout()
		return ax

	def brighten_image(self, image: numpy.ndarray) -> numpy.ndarray:
		pass

	def scatter(self, coordinates: numpy.ndarray, colors: List[str], which: ImageSelection):
		ax = self._get_ax(which)
		ax.scatter(coordinates[:, 0], coordinates[:, 1], color = colors[:len(coordinates)], s = 100)


class ImagePlotMulti(ImagePlot):
	def show_image_channel(self, channel: numpy.ndarray, ax: plt.Axes) -> plt.Axes:
		ax.imshow(channel, cmap = 'gray')
		return ax

	def show_image_coordinates(self, coordinates: numpy.ndarray, ax: plt.Axes) -> plt.Axes:
		ax.scatter(coordinates[:, 0], coordinates[:, 1])
		return ax

	def show_image_regions(self, regions: List[roifile.ImagejRoi], ax: plt.Axes) -> plt.Axes:
		colormap = {region.name: "#AAAAAA" for region in regions}
		plotter = graphics.RegionPlot(ax)
		plotter.add_regions(regions, colormap = colormap)
		# ax = regionplot.plot_region_polygons_pyplot(regions, colormap, ax = ax)
		return plotter.ax

	def show_image(self, image, which: ImageSelection, kind: ImageFormats = 'channel', label: str = None) -> plt.Axes:
		logger.debug(f"image type: {type(image)}, which = {which}, kind = {kind}")

		# If the image has a very large intensity in one location, the image will appear very dark when plotted
		# So, clip the intensities to avoidthis.

		image = numpy.clip(image, 0, 1)

		ax = self._get_ax(which)

		if kind == 'channel':
			ax = self.show_image_channel(image, ax)
		elif kind == 'coordinates':
			ax = self.show_image_coordinates(image, ax = ax)
		elif kind == 'regions':
			ax = self.show_image_regions(image, ax = ax)
		else:
			message = f"Invalid image type: {kind}"
			raise ValueError(message)
		if label:
			ax.set_title(label)
		ax.grid(False)
		plt.tight_layout()
		return ax


def main():
	pass


if __name__ == "__main__":
	main()
