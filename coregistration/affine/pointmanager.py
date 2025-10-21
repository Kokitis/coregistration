import random
from typing import *

import numpy
from loguru import logger

from . import affinetransform

PointType = Tuple[Union[int, float], Union[int, float]]


class EventType(TypedDict):
	button: Any
	canvas: Any
	dblclick: bool
	guiEvent: Any
	inaxes: Any
	key: None
	name: str
	step: int
	x: int
	y: int
	xdata: float
	ydata: float


class PointManager:  # a simple class to store selected points
	def __init__(self, barcode_left: str = None, barcode_right: str = None):
		self.label_left = 'left'
		self.label_right = 'right'
		self.barcode_left = barcode_left
		self.barcode_right = barcode_right
		self.coordinates_left = list()
		self.coordinates_right = list()

		# Maps the id of an axes object to a coordinate system.
		self._axis_labels: Dict[int, str] = dict()

		self.counter = 0  # Used to make sure both lists remain the same size
		# Saves a unique color for each pair. The index of the color corresponds to the index of each point in left and right.

		# Use a preexisting palette for the points since useing random colors can be a bit meh.
		tab_colors = [f"tab:{i}" for i in
					  ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'olive', 'cyan']]
		self.colors = tab_colors + [get_random_color() for _ in range(100)]

		# Keep a record of the last point added
		self._last_point_added = None

	def add_point(self, point: PointType, kind: Literal[None, 'left', 'right'] = None):

		if kind == 'left':
			self.coordinates_left.append(point)
		elif kind == 'right':
			self.coordinates_right.append(point)
		elif kind is None:
			print(point)
		else:
			message = f"Please specify one of ['left', 'right] (recieved {kind})"
			raise ValueError(message)
		logger.debug(f"Added {point} from {kind}")
		self._last_point_added = (point, kind)

	def remove_last_point(self):
		last_point, last_location = self._last_point_added

		if last_location == 'left':
			self.coordinates_left.pop()
		elif last_location == 'right':
			self.coordinates_right.pop()
		else:
			message = f"Cannot remove the last point due to an invalid location: {last_location}"
			raise ValueError(message)

	def add_pair(self, left: PointType, right: PointType):
		self.add_point(left, 'left')
		self.add_point(right, 'right')

	def get_points(self) -> Tuple[List[PointType], List[PointType], List[str]]:
		return self.coordinates_left, self.coordinates_right, self.colors

	def _check_coordinates(self, kind: str):
		if len(self.coordinates_left) > len(self.coordinates_right):
			# The added point is supposed to go into the smaller list
			# In this case, the right list
			if kind != 'right':
				message = f"Expected to add a point to the right image, but received a point to the left."
				logger.error(message)
				coordinate_type = None
			else:
				# self.add_point(coordinate, 'right')
				coordinate_type = 'right'
		elif len(self.coordinates_left) < len(self.coordinates_right):
			if kind != 'left':
				message = f"Expected to add a point to the left image, but received a point to the right."
				logger.error(message)
				coordinate_type = None
			else:
				coordinate_type = 'left'
		else:
			message = f"Adding point to {kind}"
			logger.debug(message)
			coordinate_type = kind
		return coordinate_type

	def register_axes(self, axis_id: int, which: Literal['left', 'right']):
		""" Registers the plt.Axes object with the given id (ex. id(object)) to the given label"""
		self._axis_labels[axis_id] = which

	def get_axis_name(self, variables: EventType) -> str:
		key = id(variables['inaxes'])
		_d = list(self._axis_labels.keys())
		print(_d)
		logger.debug(key)
		for i in _d:
			logger.debug(i)

		return self._axis_labels[key]

	def get_axis_name_obs(self, variables: EventType) -> str:
		axis_id = id(variables['inaxes'])
		keys = [self.label_left, self.label_right]
		# Get the first available label
		for label in keys:
			if label not in self._axis_labels.values():
				self._axis_labels[axis_id] = label
				break
		else:
			message = f"Found an extra axes object: {axis_id}, ({variables['inaxes']})"
			raise ValueError(message)
		return self._axis_labels[axis_id]

	def add_coordinates(self, event):
		#
		# button_press_event: xy=(768, 185) xydata=(926.2581733041411, 1132.8385724415032) button=1 dblclick=False inaxes=AxesSubplot(0.577145,0.104087;0.376883x0.839484)
		# button_press_event: xy=(504, 194) xydata=(None, None) button=1 dblclick=False inaxes=None
		# button_press_event: xy=(455, 227) xydata=(1785.5104966586518, 1032.777121247932) button=1 dblclick=False inaxes=AxesSubplot(0.0829784,0.104087;0.376883x0.839484)
		print(event)
		variables: EventType = vars(event)

		click_x = variables['x']
		click_y = variables['y']

		coordinate = (variables['xdata'], variables['ydata'])
		_values = [click_x, click_y, variables['xdata'], variables['ydata']]
		if any([i is None for i in _values]):
			return None

		axes_name = self.get_axis_name(variables)
		kind = self._check_coordinates(axes_name)
		self.add_point(coordinate, kind)

	def get_current_parameters(self):
		coordinates = list()
		for left, right in zip(self.coordinates_left, self.coordinates_right):
			xl, yl = left
			xr, yr = right
			row = {
				'barcode:left': self.barcode_left,
				'barcode:right': self.barcode_right,
				'left:x': xl,
				'left:y': yl,
				'right:x': xr,
				'right:y': yr
			}
			coordinates.append(row)
		coords_left = numpy.array(self.coordinates_left)
		coords_right = numpy.array(self.coordinates_right)

		solution = affinetransform.solve_affine(coords_left, coords_right)

		result = {
			'transform': solution,
			'transform:coordinates': coordinates,
			'transform:parameters': solution.to_parameters(),
			'transform:matrix': solution.to_matrix().tolist()
		}
		return result


def get_random_color(lower: int = 50, upper: int = 250) -> str:
	red = random.randint(lower, upper)
	green = random.randint(lower, upper)
	blue = random.randint(lower, upper)
	return f"#{red:>02X}{green:>02X}{blue:>02X}"
