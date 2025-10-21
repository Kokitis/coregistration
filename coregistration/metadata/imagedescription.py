from pathlib import Path
from typing import *
from loguru import logger
import json
import xmltodict
from bs4 import BeautifulSoup
import tifffile

DEFAULT_PREFIX = "@"


def coerce_to_dict(content: Union[str, Dict, List, Path], attr_prefix: str = DEFAULT_PREFIX) -> Dict:
	"""
		Tries to convert the input data into a dict object.
	"""
	if isinstance(content, str):
		content_is_xml = is_xml(content)
		# Convert to dict
		if content_is_xml:
			result = convert_xml_to_json(content, attr_prefix = attr_prefix)
		else:
			result = json.loads(content)
	elif isinstance(content, dict):
		result = content
	elif isinstance(content, list):
		result = {index: value for index, value in enumerate(content)}
	elif isinstance(content, Path):
		result = get_all_descriptions(content)
		result = {key: coerce_to_dict(value, attr_prefix = attr_prefix) for key, value in result.items()}
	else:
		message = f"Can't convert this to dict {type(content)=}"
		raise ValueError(message)
	return result


def is_json(data: Union[str, Path, Dict]) -> bool:
	if isinstance(data, Path):
		result = data.suffix in {'.json', 'geojson'}
	elif isinstance(data, dict):
		result = True
	elif isinstance(data, str):
		result = data.startswith('{') or data.startswith('[')
	else:
		logger.warning(f"Unusual type: {type(data)}")
		result = False
	return result


def is_xml(data: Union[str, Path, Dict]) -> bool:
	if isinstance(data, Path):
		result = data.suffix in {'.xml', '.html'}
	elif isinstance(data, dict):
		result = False
	elif isinstance(data, str):
		result = data.startswith('<OME') or data.startswith("<?xml")
	else:
		logger.warning(f"Unusual type: {type(data)}")
		result = False
	return result


def convert_xml_to_json(text: str, attr_prefix: str = DEFAULT_PREFIX):
	"""
		Converts the input xml document into a dictionary
	"""
	# The xml text may have some weird characters on the end. Need to remove them.
	while not text.endswith('>'):
		text = text[:-1]
	try:
		result = xmltodict.parse(text, attr_prefix = attr_prefix)
	except Exception as exception:
		message = f"Encountered error when converting to dict: '{exception}'"
		logger.error(message)
		raise exception
	# xmltodict returns ordered dicts, which are harder to read than regular dictionaries.
	result = json.loads(json.dumps(result))
	return result


def get_description_format(description: Union[str, Dict]) -> Literal['data', 'json', 'xml']:
	if isinstance(description, dict):
		data_format: Literal['data'] = 'data'
	else:
		if is_xml(description):
			data_format: Literal['xml'] = 'xml'
		elif is_json(description):
			data_format: Literal['json'] = 'json'
		else:
			message = f"Unknown description format"
			raise ValueError(message)
	return data_format


def get_description_source(io: Union[str, Dict[str, Any]]) -> Literal['perkins', 'ome']:
	"""
		Determines the source of the description, which affects how it must be parsed.
	"""

	if "PerkinElmer-QPI-ImageDescription" in io:
		description_source: Literal['perkins'] = 'perkins'
	elif 'OME' in io:
		description_source: Literal['ome'] = 'ome'
	elif isinstance(io, dict) and ('Name' in io and 'Color' in io):
		description_source: Literal['perkins'] = 'perkins'
	elif isinstance(io, dict) and 'Image' in io:
		description_source: Literal['ome'] = 'ome'
	else:
		message = f"Cannot determine the the source of the description."
		raise ValueError(message)
	return description_source


def get_data_type(io: Union[str, Path, Dict[str, Any]]):
	if isinstance(io, Path):
		descriptions = get_all_descriptions(io)
		description = descriptions[0]['text']
		description_source = get_description_source(description)
		description_format = get_description_format(description)
		data_type = f"image-{description_source}-{description_format}"
	elif isinstance(io, str):
		description_source = get_description_source(io)
		description_format = get_description_format(io)
		data_type = f"string-{description_source}-{description_format}"
	elif isinstance(io, dict):
		description_source = get_description_source(io)
		data_type = f'data-{description_source}'
	else:
		message = f"Cannot determin the data source/format! ({type(io)=})"
		raise ValueError(message)
	return data_type


def get_name_from_description(description: Union[str, BeautifulSoup]) -> Optional[str]:
	if isinstance(description, str):
		soup = BeautifulSoup(description, features = 'xml')
	else:
		soup = description
	name = soup.find('Name')
	if name is None:
		name = soup.find('name')
	if name is None:
		name = soup.find('Marker')
	if name is not None:
		name = name.text

	return name


def get_all_descriptions(filename: Path) -> Dict[int, Dict[str, Any]]:
	results = dict()
	with tifffile.TiffFile(filename) as tif:
		for index, page in enumerate(tif.pages):
			description = page.tags.get(270)
			if description:
				description = description.value

			record = {
				'text':  description,
				'index': index,
				'path':  filename
			}
			results[index] = record
	return results


def get_description_from_page(page: tifffile.TiffPage) -> str:
	""" Retrieves the 'ImageDescription' tag from the page. Returns `''` if no description is found. """

	description_tag = page.tags.get(270)
	if description_tag:
		description_tag = description_tag.value
	else:
		description_tag = ""
	return description_tag


def main():
	pass


if __name__ == "__main__":
	main()
