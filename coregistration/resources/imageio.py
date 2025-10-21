from pathlib import Path
from typing import *

import numpy
# import roifile

import tifffile
from loguru import logger
from coregistration import dataio, metadata

# from vectratools import arraytools, dataio, metadata
# from vectratools.utilities import tifftools

DEFAULT_FILLVALUE = None


class Image:
	"""
		Handles the .tiff files.
		Parameters
		----------
		image: Union[str, Path, numpy.ndarray]
			The input image.
		channels: Dict[str,str]
			A list of `ChannelInfo` items. If it's a dictionary it will be converted to a list using the `.values()` method. The identifier should be left to the `Image`
			class to generate dynamically, if possible, to avoid minor problems.
		channel_map: Dict[str,int]
		barcode:str = None
			An optional barcode to give the image. If `None`, the input image file name will be used, if available.
		norm:bool
		clip:bool
	"""

	def __init__(
			self, image: Union[numpy.array, Path, str], channels: Dict[str, metadata.ChannelData] = None,
			channel_map: Dict[str, int] = None, barcode: str = None, tags: Dict[int, tifffile.TiffTag] = None, norm: bool = False, clip: bool = False):

		self.is_norm = norm
		self.is_clip = clip
		self.resolution_code = 1  # Indicates what the downscale factor is if the source is a wholeslide image.

		if isinstance(image, (str, Path)):
			self.filename = Path(image)

			self.data: numpy.ndarray = dataio.read_array(self.filename, norm = norm, clip = clip)
			self.tags = metadata.get_image_tags(self.filename).get(0, {})
			self.channels: Dict[str, metadata.ChannelData] = metadata.get_channel_data(self.filename)
		else:
			self.filename = None
			self.data = image
			self.tags = tags if tags is not None else {}
			self.channels: Dict[str, metadata.ChannelData] = self._process_channel_info(channels)
		self.barcode = barcode if barcode else (self.filename.stem if self.filename else None)
		if channel_map is None:
			self.channel_name_map = self._generate_channel_name_map()
		else:
			self.channel_name_map = channel_map

		# Check if the `data` attribute is an image with a single channel. If so, convert it to a 3D array with a single member.
		if self.data.ndim == 2:
			y, x = self.data.shape
			self.data = self.data.reshape((1, y, x))

	def _process_channel_info(self, channels: Union[List[metadata.ChannelData], Dict[str, metadata.ChannelData]] = None) -> Dict[str, metadata.ChannelData]:

		if channels is None:
			if self.filename is None:
				channels = dict()
			else:
				# channels = metadata.read_image_metadata(self.filename)
				channels = metadata.get_channel_data(self.filename)

		if isinstance(channels, dict) and all(isinstance(i, int) for i in channels.keys()):
			channels = list(channels.values())

		if isinstance(channels, list):
			# Some images represent the same channel twice with different resolutions (ex. '.svs' files). The channels
			# are generally ordered with the largest representations appearing first, so any subsequent channels for a marker should be ignored.
			# Remove any None

			channels = [i for i in channels if i is not None]

			channellist = list()
			seen = set()

			for info in channels:
				marker_name = info['marker']
				if marker_name not in seen:
					seen.add(marker_name)
					channellist.append(info)
			channels = {value['marker']: value for value in channellist if value}

		# Check if `channels` is a ChannelData object for an image with only one channel
		if 'marker' in channels:
			marker = channels['marker']
			channels = {channels['marker']: channels}
			# Insert the default index
			channels[marker]['index'] = 0
			return channels
		# Remove the channels that don't correspond to our markers.
		channels = {key: value for key, value in channels.items() if not key.startswith('Channel')}
		self.channels = channels
		return channels

	def _generate_channel_name_map(self) -> Optional[Dict[Union[int, str], Union[int, str]]]:

		if self.channels is not None:
			result = dict()

			for channel in self.channels.values():
				if channel is None:
					continue
				channel_name = channel['name']

				channel_index: int = channel['index']
				channel_name_short = channel['marker'].split(" ")[0]
				# Check whether the name already exists in the channel map. Some of the files have duplicate entries in the 'pages' attribute when
				# reading them with tifffile, but the actual image data only has the expected 8 channels. So ignore the repeats.
				if channel_name not in result:
					result[channel_name] = channel_index
					result[channel_name_short] = channel_index
					result[channel_index] = channel_name

		else:
			result = None

		return result

	def normalize(self) -> Self:
		self.data = dataio.read_array(self.data)
		return self

	@property
	def channel_count(self) -> int:
		return self.data.shape[0]

	@property
	def multichannel(self) -> bool:
		return self.data.ndim != 2

	@property
	def shape(self) -> Tuple[int, int, int]:
		return self.data.shape

	def get_channel(self, index: Union[str, int]) -> Optional[numpy.ndarray]:
		if isinstance(index, str):
			index = self.channel_name_map.get(index)
		if index is None:
			return None
		try:
			array = self.data[index, :, :]
		except IndexError as exception:
			message = f"The index ({index}) is out of bounds for an array with shape {self.data.shape}"
			logger.error(message)
			raise exception

		return array


def get_dimension(shape: Tuple, order: Literal['xyz', 'zyx'] = 'zyx') -> Dict[str, int]:
	# Array shape is usually stored as ZYX
	if len(shape) == 2:
		result = {
			'x': shape[1],
			'y': shape[0],
			'z': None
		}
	else:
		result = dict(zip(order, shape))

	# raise ValueError(f"Invalid index for {shape}: {which=}")
	return result


if __name__ == "__main__":
	import matplotlib.pyplot as plt

	path = Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/images/merged/images/d10sA2t17.tif")
	image = Image(path)
	channel = image.get_channel("Brightfield")
	fig, ax = plt.subplots(figsize = (20, 10))
	ax.imshow(channel, cmap = 'gray')
	plt.show()
