from pathlib import Path
from typing import *

import numpy
import tifffile
from bs4 import BeautifulSoup


def _parse_color_string(text: str) -> str:
	""" Converts the color specified in the tiff file to hex format. The color is usually formtted as '255,0,255'"""

	string_red, string_green, string_blue = text.split(',')
	value_red, value_green, value_blue = int(string_red), int(string_green), int(string_blue)

	color = f"#{value_red:>02X}{value_green:>02X}{value_blue:>02X}"
	return color


class Image:
	"""
		Handles the .tiff files.
	"""

	def __init__(self, image: Union[numpy.array, Path, str], channels: Dict[int, Dict[str, str]] = None,
			channel_map: Dict[str, int] = None, norm: bool = True
	):
		if isinstance(image, (str, Path)):
			self.filename = Path(image)
			self.data: numpy.ndarray = tifffile.imread(image)
			#if norm:
			#	self.data: numpy.ndarray = normalize(self.data, 1, 99.8, axis = (0, 1))

			if channels is None:
				self.channels = self.read_channels(image)
			else:
				self.channels = channels

		else:
			self.filename = None
			self.data = image
			self.channels = channels

		if channel_map is None:
			self._channel_name_map = self._generate_channel_name_map()
		else:
			self._channel_name_map = channel_map

		# Convert the channels attribut from a dictionary of indeces to a dictionary of channel names.
		# This will amke things a lot simpler in other parts of the code.
		if self.channels:
			self.channels = {value['name']: value for value in self.channels.values()}

	def _fix_training_info(self):
		""" Fixes the channels and channel name map for the images in the training set which are missing channel information."""
		# Check if it's a trainnig image.
		if 'Channel 1' not in self._channel_name_map: return None

		if self.filename is not None and self.filename.name.split("_")[1] == '4203':
			self._channel_name_map = {
				'PD-1': 0,
				'SOX10': 1,
				'CD68': 2,
				'DAPI': 3,
				'CD3': 4,
				'CD8': 5,
				'PD-L1': 6,
				'Autoflourescence': 7
			}

			self.channels = {
				0: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#00FFFF',
					'index': 0,
					'name': 'PD-1 (Opal 570)'
				},
				1: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#FF8000',
					'index': 1,
					'name': 'SOX10 (Opal 620)'
				},
				2: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#FF0000',
					'index': 2,
					'name': 'CD68 (Opal 690)'
				},
				3: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#0000FF',
					'index': 3,
					'name': 'DAPI'
				},
				4: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#00FF00',
					'index': 4,
					'name': 'CD3 (Opal 520)'
				},
				5: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#FFFF00',
					'index': 5,
					'name': 'CD8 (Opal 540)'
				},
				6: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#FF00FF',
					'index': 6,
					'name': 'PD-L1 (Opal 650)'
				},
				7: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': '#2F4F4F',
					'index': 7,
					'name': 'Autofluorescence'
				},
				8: {
					'barcode': 'Macro_4203_IF_09_04_19_[8086,61210]',
					'color': None,
					'index': 8,
					'name': 'Channel 8'
				}
			}

	def _generate_channel_name_map(self) -> Optional[Dict[str, int]]:
		if self.channels is not None:
			result = dict()
			for channel in self.channels.values():
				channel_name = channel['name']
				channel_index: int = channel['index']
				channel_name_short = channel['name'].split(" ")[0]  # Ex. 'CD3 (Opal 670)' -> 'CD3'
				# Check whether the name already exists in the channel map. Some of the files have duplicate entries in the 'pages' attribute when
				# reading them with tifffile, but the actual image data only has the expected 8 channels. So ignore the repeats.
				if channel_name not in result:
					result[channel_name] = channel_index
					result[channel_name_short] = channel_index
		else:
			result = None

		return result

	@staticmethod
	def parse_description(text: Optional[str]) -> Optional[Dict[str, str]]:
		if text is not None:
			soup = BeautifulSoup(text, 'lxml')
			barcode = soup.find('slideid')
			name = soup.find('name')
			color = soup.find('color')
		else:
			barcode = name = color = None

		result = {
			'name': name.text.split(' ')[0] if name else None,
			'longName': name.text if name else None,
			'colorOriginal': color.text if color else None,
			'color': _parse_color_string(color.text) if color else None,
			'barcode': barcode.text if barcode else None
		}
		return result

	def read_channels(self, filename: Path) -> Dict[int, Dict[str, str]]:
		""" Extracts channel information from the tiff file."""

		channels = dict()
		with tifffile.TiffFile(filename) as tiff:
			for index, page in enumerate(tiff.pages):
				description = page.tags.get('ImageDescription')
				result = self.parse_description(description.value if description else None)
				result['index'] = index
				if result['name'] is None: result['name'] = f"Channel {index}"

				channels[index] = result
		return channels

	@property
	def channel_count(self) -> int:
		return self.data.shape[0] if self.multichannel else 1

	@property
	def multichannel(self) -> bool:
		return self.data.ndim != 2

	@property
	def shape(self) -> Tuple[int, int]:
		if self.multichannel:
			# THe shape is returned as y, x, so need to reverse it.
			return self.data.shape[2], self.data.shape[1]
		else:
			return self.data.shape[1], self.data.shape[0]

	def get_channel_info(self, label: Union[str, int]) -> Dict[str, str]:
		label = self._channel_name_map.get(label, label)
		return self.channels[label]

	def check_index(self, value: Union[int, Tuple[int, int]], axis: Literal['x', 'y'] = None):
		if isinstance(value, tuple):
			result = self.check_index(value[0], 'x'), self.check_index(value[1], 'y')
		else:
			minimum = 0
			maximum = self.shape[0] if axis == 'x' else self.shape[1]
			if value < minimum:
				result = minimum
			elif value > maximum:
				result = maximum
			else:
				result = value
		return result

	def get_slice(self, xlims: Tuple[int, int], ylims: Tuple[int, int], border: int = 0) -> 'Image':
		"""	Extracts a rectangular region of an image based on the given x and y limits.
			The image slice will include the pixels located at the maximum of the x and y ranges.
		"""
		left = self.check_index(xlims[0] - border, 'x')
		right = self.check_index(xlims[1] + border + 1, 'x')
		top = self.check_index(ylims[0] - border, 'y')
		bottom = self.check_index(ylims[1] + border + 1, 'y')
		# logger.debug(f"Border: {border}")
		# logger.debug(f"Image shape: {self.shape}")
		# logger.debug(f"Getting slice with bounds {left, right, top, bottom}")
		if self.multichannel:
			subarray = self.data[:, top:bottom, left:right]
		else:
			subarray = self.data[top:bottom, left:right]

		return Image(subarray, channels = self.channels, channel_map = self._channel_name_map)

	def get_channel(self, label: Union[int, str]) -> numpy.array:
		""" Retrieves the specified channel."""
		if self.multichannel:
			if isinstance(label, str):
				index = self._channel_name_map.get(label)
				if index is None:
					message = f"Not a valid channel name: '{label}'. Expected one of {sorted(self._channel_name_map.keys())}"
					raise ValueError(message)
			elif isinstance(label, int):
				index = label
			else:
				message = f"Invalid channel label: '{label}' (type: {type(label)})"
				raise ValueError(message)
			result = self.data[index]
		else:
			result = self.data
		return result

	def set_channels(self, channels: Dict):
		pass

	def show_channels(self):
		import matplotlib.pyplot as plt

		number_of_columns = 3
		number_of_rows = int(self.channel_count / 3) + 1
		fig, axes = plt.subplots(number_of_rows, number_of_columns, figsize = (16, 16))

		for index in range(self.channel_count):
			ix, iy = divmod(index, number_of_columns)
			ax = axes[ix, iy]
			channel = self.get_channel(index)
			ax.imshow(channel, cmap = 'gray')
			ax.set_axis_off()
			ax.set_title(self.channels[index]['name'])

		plt.tight_layout()
		plt.show()
