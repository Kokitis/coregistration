from pathlib import Path
from typing import *
import tifffile
import math
import pandas
import numpy

RESOLUTION_UNIT_CODES = {
	'NONE':       1,
	'INCH':       2,
	'CENTIMETER': 3,
	'MILLIMETER': 4,
	'MICROMETER': 5,

	'cm':         3,
	'mm':         4,
	'µm':         5,
	'um':         5

}

RESOLUTION_UNITS = {
	'CENTIMETER': 1E-4,
	'MILLIMETER': 1E-3,
	'MICROMETER': 1,
	'INCH':       2.54E-4,
	'NONE':       math.nan,
	'mm':         1E-3,
	'cm':         1E-4,
	'µm':         1,
	'um':         1
}
TAGNAMES = {
	254: 'SubfileType',
	256: 'ImageWidth',
	257: 'ImageLength',
	258: 'BitsPerSample',
	259: 'Compression',
	262: 'PhotometricInterpretation',  # Colorspace of the image
	270: 'ImageDescription',
	273: 'StripOffsets',  # Byte offset
	277: 'SamplePerPixel',
	278: 'RowsPerStrip',
	279: 'StripByteCounts',
	282: 'XResolution',  # pixels per resolution unit
	283: 'YResolution',
	284: 'PlanarConfiguration',
	286: 'XPosition',
	287: 'YPosition',
	296: 'ResolutionUnit',  # Unit of measurement for X/YResolution
	305: 'Software',
	306: 'DateTime',
	339: 'SampleFormat',
	340: 'SMinSampleValue',
	341: 'SMaxSampleValue'
}
TAGNAMES = {k: v for k, v in TAGNAMES.items()} | {v: k for k, v in TAGNAMES.items()}

TAG_CONFIG = {
	258: {
		'name':       'BitsPerSample',
		'code':       258,
		'count':      1,
		'dataformat': '1H',
		'dtype':      3,
		'valueType':  "int|tuple"
	},
	259: {
		'name':       'Compression',
		'code':       259,
		'count':      1,
		'dataformat': '1H',
		'dtype':      3,
		'valueType':  "enum:COMPRESSION->LZW|None"
	},
	306: {
		'name':       'DateTime',
		'code':       306,
		'count':      20,
		'dataformat': '1s',
		'dtype':      2,
		'valueType':  'str'
	},
	257: {
		'name':       'ImageLength',
		'code':       257,
		'count':      1,
		'dataformat': '1H|1I',
		'dtype':      (3, 4),
		'valueType':  'int'
	}
}


def calculate_resolution_factor_from_ome(image_metadata: Dict[str, str | int | float]) -> Tuple[float, float]:
	"""
		Uses a dictionary of OME image metadata to calculate the number of pixels per micrometer in the x and y axes.
		Parameters
		----------
		image_metadata: Dict[str,str|int|float]
			Requires the following keys:
			- `PhysicalSizeX`
			- 'PhysicalSizeXUnit`
			- `PhysicalSizeY`
			- `PhysicalSizeYUnit`
		Returns
		-------
		Tuple[float, float]
			The number of pixels per micrometer in the x and y axes.
	"""
	physical_per_pixel_x = image_metadata['PhysicalSizeX']
	physical_per_pixel_x_units = image_metadata['PhysicalSizeXUnit']
	physical_units_per_micrometer_x = RESOLUTION_UNITS[physical_per_pixel_x_units]

	physical_per_pixel_y = image_metadata['PhysicalSizeY']
	physical_per_pixel_y_units = image_metadata['PhysicalSizeYUnit']
	physical_units_per_micrometer_y = RESOLUTION_UNITS[physical_per_pixel_y_units]

	pixels_per_micrometer_x = 1 / (physical_per_pixel_x * physical_units_per_micrometer_x)
	pixels_per_micrometer_y = 1 / (physical_per_pixel_y * physical_units_per_micrometer_y)

	return pixels_per_micrometer_x, pixels_per_micrometer_y


def generate_tags_ome(array: numpy.ndarray, ome_metadata: Dict[str, str | int | float]):
	tags = list()
	image_width = array.shape[-1]
	image_height = array.shape[-2]

	physical_per_pixel_x = ome_metadata['PhysicalSizeX']
	physical_per_pixel_x_units = ome_metadata['PhysicalSizeXUnits']

	physical_per_pixel_y = ome_metadata['PhysicalSizeY']
	physical_per_pixel_y_units = ome_metadata['PhysicalSizeYUnits']

	pixels_per_micrometer_x, pixels_per_micrometer_y = calculate_resolution_factor_from_ome(ome_metadata)

	micrometers_per_pixel_x = 1 / pixels_per_micrometer_x
	micrometers_per_pixel_y = 1 / pixels_per_micrometer_y

	image_width_in_micrometers = image_width / pixels_per_micrometer_x
	image_height_in_micrometers = image_height / pixels_per_micrometer_y


# tags.append((282, tifffile.DA))


def get_image_tags(path: Path) -> Dict[int, Dict[int, tifffile.TiffTag]]:
	"""
		Returns the `tifffile.TiffTag` objects associated with each channel in the image.
	"""
	image_tags = dict()
	with tifffile.TiffFile(path) as tif:
		for index, page in enumerate(tif.pages):
			image_tags[index] = page.tags
	return image_tags


def get_resolution_scalefactor_from_description(description: str) -> Tuple[float, float]:
	pass

def get_resolution_factor(io: str | Path | Dict[int, tifffile.TiffTag], extractor:Callable[[str], Tuple[float, float]] = None)->Tuple[float, float]:
	"""
		Extracts the number of pixels per micrometer in the x and y axes.
	Parameters
	----------
	io: Path
		Path to the image.

	Returns
	-------
	Tuple[float, float]
		The x and y resolution factors.
	"""

	if isinstance(io, dict):
		image_tags = io
	else:
		image_tags = get_image_tags(io)[0]

	# Try to calculate the resolution factor from the image tags.
	# Should be the most accurate way to calculate the resolution factor,
	# But some tif files have a custom format and don't provide the correct metadata.
	try:
		result = calculate_resolution_factor(image_tags)
	except KeyError:
		result = None

	if result is None and isinstance(io, Path) and extractor is not None:
		# Try to extract the information from the image description.
		descriptions = dict()
		with tifffile.TiffFile(io) as tif:
			for index, page in enumerate(tif.pages):
				d = page.tags.get(270)
				if d:
					descriptions[index] = d.value

		description = descriptions[0]
		result = extractor(description)

	return result








def calculate_resolution_factor(tags: Dict[int, tifffile.TiffTag]) -> Tuple[float, float]:
	"""
		Calculates the number of pixels per micrometer from the available tags.
		Parameters
		----------
		tags: Dict[int, tifffile.TiffTag]
			The image tags.

		Returns
		-------
		Tuple[float,float]
			The `x` and `y` scalefactor.
	"""
	try:
		resolution_unit = tags[296].value.name
		if resolution_unit == 'NONE':
			resolution_unit = 'CENTIMETER'
	except KeyError:
		resolution_unit = 'CENTIMETER'
	x_width, x_width_unit = tags[282].value
	y_width, y_width_unit = tags[283].value

	unit_x = RESOLUTION_UNITS[resolution_unit] * x_width / x_width_unit
	unit_y = RESOLUTION_UNITS[resolution_unit] * y_width / y_width_unit

	return unit_x, unit_y


def get_image_metadata(path: Path, astable: bool = False) -> Dict[int, Dict[str, Any]] | pandas.DataFrame:
	"""
		Extracts the tiff tags (https://www.loc.gov/preservation/digital/formats/content/tiff_tags.shtml) for each channel
	Parameters
	----------
	path: Path
		Path to a tiff file.

	Returns
	-------
	Dict[str, Dict[int, Any]
		Each key (formatted as 'channel-{index}') maps to a dictionary of tiff tags.
	"""

	records = list()

	image_tags = get_image_tags(path)

	for page_index, page_tags in image_tags.items():

		for tag_code, tag in page_tags.items():
			if tag_code in {270, 273, 279, 324, 325}:
				continue

			try:
				name = tag.value.name
				value = tag.value.value
			except AttributeError:
				name = None
				value = tag.value

			record = {
				'image':       path.name,
				'page':        f"page-{page_index}",
				'code':        tag.code,
				'count':       tag.count,
				'dataformat':  tag.dataformat,
				'dtype':       tag.dtype,
				'name':        tag.name,
				'value':       tag.value,
				'offset':      tag.offset,
				'valueOffset': tag.valueoffset,
				'type':        type(tag.value),
				'subName':     name,
				'subValue':    value
			}
			records.append(record)
	if astable:
		result = pandas.DataFrame(records)
	else:
		result = {item['code']: item for item in records}
	return result


def format_extra_tags(tags: Dict[str, tifffile.TiffTag]) -> Dict[str, Tuple[int, str, Any, Union[int, float, str]]]:
	"""
		Converts tifffile.TiffTag objects into the format required by the tifffile extra tag parameters.
	"""

	extra_tags = list()
	for tag_code, tag in tags.items():
		result = (tag.code, tag.dtype, tag.count, tag.value)
		extra_tags.append(result)
	return extra_tags


def get_all_tags(path: Path):
	blacklist = {'TileByteCounts', 'TileOffsets', 'StripOffsets', 'StripByteCounts'}
	all_tags = dict()
	with tifffile.TiffFile(path) as tif:
		for index_page, page in enumerate(tif.pages):
			page_tags = dict()
			for key, tag in page.tags.items():
				record = {
					'indexPage': index_page,
					'name':      tag.name,
					'code':      tag.code,
					'dtype':     tag.dtype,
					'count':     tag.count,
					'value':     tag.value
				}
				if tag.name not in blacklist:
					page_tags[key] = record

			all_tags[index_page] = page_tags

	return all_tags
