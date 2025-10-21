"""
	Categorizes the input into categories based on what needs to be done to get it into the proper format.

	if path is an image: extract the description normally.
	if path is text, assume it contains the description for a single channel
	if path is json, assume it contains the data for a description.
	if path is xml, assume it contains xml data for a description

	- 'path-tif': The channel descriptions need to be extracted from the image tags.
	- 'path-txt: Assume the file contains a single description.
	- 'path-json': Assume the input data came from a previous inspection.
	- 'path-xml': Assume it is an xml-formatted channel description.
	- 'string-xml-ome': Convert to a dictionary using xmltodict
	- 'string-xml-perkins': Convert to a dictionary using xmltodict.
	- 'string-json': Load the data into memory.
	- 'data-perkins': A dictionary structured according to the standard Perkins XML format.
	- 'data-ome': A dictionary structured according to the standard OME-XML format.
	- 'json-dsp': A DSP description which was converted to json via `xmltodict`
	- 'data-id': A more concise version of 'data-ome'
	- 'data-channels: A Dictionary mapping page indices to channel descriptions.
	- 'data-channels-list: A list of channel descriptions
"""

from pathlib import Path
from typing import *

try:
	from coregistration.metadata import imagedescription, schemaperkins, schemaome
except ModuleNotFoundError:
	import imagedescription, schemaperkins, schemaome

DescriptionFormatType = NewType("DescriptionFormatType", str)
DescriptionFormatKeys = [
	'path-image',
	'path-xml',
	'path-json',

	'string-xml-perkins',
	'string-xml-ome',
	'string-xml-id',
	'string-json',
	'string-json-ome',

	'data-channels',
	'data-structured',
	'data-json-perkins',
	'data-json-ome',
	'data-id'
]


class DescriptionTypes:
	# Path types
	path_image = 'path-image'
	path_xml = 'path-xml'
	path_json = 'path-json'
	# Text formats
	string_xml_perkins = 'string-xml-perkins'
	string_xml_ome = 'string-xml-ome'
	string_xml_id = 'string-xml-id'
	string_json = 'string-json'
	string_json_ome = 'string-json'

	# Dict Types
	data_ome_channels = 'data-ome-channels'
	data_json_perkins = 'data-json-perkins'
	data_json_ome = 'data-json-ome'

	data_json_perkins_description = "data-json-perkins-description"  # A description with information for all channels
	data_json_perkins_channel = 'data-json-perkins-channel'
	data_json_perkins_channellist = 'data-json-perkins-channellist'
	data_json_perkins_channelmap = 'data-json-perkins-channelmap'  # A mapping of page index to page descriptions.

	ome_xml = 'xml-ome'
	# ome_xml_custom = 'xml-ome-custom'
	xml_perkins = 'xml-perkins'
	xml_dsp = 'xml-dsp'
	# xml_single = 'xml-perkins-single'
	# xml_multiple = 'xml-perkins-multiple'
	custom = 'custom'
	# Data formats
	data_ome = 'data-ome'
	data_custom = 'data-custom'
	data_perkins = 'data-perkins'
	data_id = "data-ID"


def parse_label(label: str) -> Tuple[str, str, str]:
	parts = label.split('-')
	if len(parts) == 3:
		data_type, data_class, data_format = parts
	else:
		data_type, data_class = parts
		data_format = None
	return data_type, data_class, data_format


def get_schema_type_ome(data: Dict[str, Any]) -> Literal['ome', 'ome-custom', 'ome-channels']:
	if 'OME' in data:
		data = data['OME']
	if 'Image' not in data:
		message = f"Invalid format: {data}"
		raise ValueError(message)
	image = data['Image']
	if 'Description' in image:
		result = 'ome-custom'
	else:
		result = 'ome'
	return result


def get_schema_type(data: Dict[str, Any]) -> Literal['perkins', 'ome', 'ome-custom', 'ome-channels']:
	if "PerkinElmer-QPI-ImageDescription" in data:
		result = 'perkins'
	elif 'OME' in data:
		result = get_schema_type_ome(data)
	else:
		message = f'Unknown description format. Keys: {sorted(data.keys())}'
		raise ValueError(message)

	return result


def get_data_type_from_path(path: Path) -> Literal['path-image', 'path-xml', 'path-json']:
	if path.suffix in {'.tif', '.tiff', '.qptiff'}:
		data_type = 'path-image'
	elif path.suffix in {'.txt', '.xml'}:
		data_type = 'path-xml'
	elif path.suffix == '.json':
		data_type = 'path-json'
	else:
		message = f"Unsupported file format : '{path.suffix}'"
		raise ValueError(message)
	return data_type


def get_data_type_from_string_xml(text: str) -> Literal['string-xml-perkins', 'string-xml-ome', 'string-xml-id']:
	if text.startswith('<?xml'):
		if 'PerkinElmer-QPI-ImageDescription' in text[:100]:
			data_type = 'string-xml-perkins'
		elif 'OME' in text[:100]:
			data_type = 'string-xml-ome'
		elif 'ImageDescription' in text[:100]:
			data_type = 'string-xml-id'
		else:
			message = f"Cannot determine the format of {text[:100]=}"
			raise ValueError(message)
	elif text.startswith('<OME'):
		data_type = 'string-xml-ome'
	else:
		message = f"Unknown string format: {text[:100]=}"
		raise ValueError(message)

	return data_type


def get_data_type_from_string_json(text: str):
	if text.startswith('[') or text.startswith('{'):
		# Check if the 'OME' key is located near the start of the file
		if 'OME' in text[:25]:
			data_type = 'string-json-ome'
		elif 'PerkinElmer-QPI-ImageDescription' in text[:50]:
			data_type = 'string-json-perkins'
		else:
			# raise ValueError(f"Unknown json format: {text[:100]=}")
			data_type = 'string-json-unknown'
	else:
		message = 'Unknown json format'
		raise ValueError(message)
	return data_type


def get_data_type_from_dict(data: Dict) -> Literal['data-channels', 'data-structured', 'data-perkins', 'data-ome', 'daata-id', 'data-list']:
	# Check if it's a dictionary mapping page indices to description strings.
	if all(isinstance(key, int) for key in data.keys()) and all(isinstance(value, str) for value in data.values()):
		data_type = 'data-channels'
	elif all((isinstance(value, dict) and len(value) == 1) for value in data.values()):
		data_type = 'data-structured'
	elif 'PerkinElmer-QPI-ImageDescription' in data:
		data_type = 'data-json-perkins'
	elif 'OME' in data:
		data_type = 'data-json-ome'
	elif 'ImageDescription' in data:
		data_type = 'data-id'
	else:
		message = f"Invalid data type: {data}"
		raise ValueError(message)
	return data_type


def get_data_type(data: Any):
	"""
		Categorizes the input into categories based on what needs to be done to get it into the proper format.

		if path is an image: extract the description normally.
		if path is text, assume it contains the description for a single channel
		if path is json, assume it contains the data for a description.
		if path is xml, assume it contains xml data for a description

		- 'path-tif': The channel descriptions need to be extracted from the image tags.
		- 'path-txt: Assume the file contains a single description.
		- 'path-json': Assume the input data came from a previous inspection.
		- 'path-xml': Assume it is an xml-formatted channel description.
		- 'string-xml-ome': Convert to a dictionary using xmltodict
		- 'string-xml-perkins': Convert to a dictionary using xmltodict.
		- 'string-json': Load the data into memory.
		- 'string-unknown': Unknown format. Only seen in one project which just had plain  text in the description.
		- 'data-perkins': A dictionary structured according to the standard Perkins XML format.
		- 'data-ome': A dictionary structured according to the standard OME-XML format.
		- 'json-dsp': A DSP description which was converted to json via `xmltodict`
		- 'data-id': A more concise version of 'data-ome'
		- 'data-channels: A Dictionary mapping page indices to channel descriptions.
		- 'data-channels-list: A list of channel descriptions
		- 'data-channels-dict: Mapping of page index to page description
	"""

	if isinstance(data, Path):
		data_type = get_data_type_from_path(data)
	elif isinstance(data, str):
		if imagedescription.is_xml(data):
			data_type = get_data_type_from_string_xml(data)
		elif imagedescription.is_json(data):
			data_type = get_data_type_from_string_json(data)
		else:
			# message = f'Unknown string format: {data}'
			# raise ValueError(message)
			data_type = 'string-unknown'

	elif isinstance(data, dict):
		data_type = get_data_type_from_dict(data)
	# Check if it's a dictionary mapping page indices to description strings.
	elif isinstance(data, list):
		data_type = 'data-list'
	else:
		message = f"Invalid data type: {data}"
		raise ValueError(message)

	return data_type


def main():
	pass


if __name__ == "__main__":
	main()
