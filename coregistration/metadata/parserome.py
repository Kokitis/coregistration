from pathlib import Path
from typing import *
from infotools import colortools
from coregistration.metadata import schemaome, schemachannel, parserbase, imagedescription
from dataclasses import asdict


class DescriptionParserOME(parserbase.DescriptionParserBase):
	"""
		Parses OME-XML data, including the modified version used in tiles.
		Tries to retrieve the channel data from the dictionary. A typical OME-XML document will save the description in obj['OME']['Image']['Description']
		However, the description will be saved as obj['OME']['Image']['Pixels']['Channel'] if it's from a multichannel tile generated from a very large image.
		The channels are formatted similar to an api, and each channel has the following format:
			- '@ID'
			- '@Name'
			- '@SamplesPerPixel'
			- 'LightPath'
	"""

	def get_unit_scale(self, text: str, **kwargs) -> Optional[float]:
		"""
			Searches the description for an explicit conversion rate from um to pixels.
		Parameters
		----------
		text

		"""
		raise NotImplementedError

	def parse_channel_item(self, channel: schemaome.ChannelSchema, **kwargs) -> schemachannel.ChannelDataClass:

		name = channel.get('_Name', channel.get("@Name"))
		marker_name, signal = schemachannel.process_name(name)
		color_value = channel.get("_Color", channel.get("@Color", -1))

		if isinstance(color_value, str) and color_value.replace('-', '').isdigit():
			# OME Stores colors as integers
			color_value = int(color_value)

		color = colortools.convert_integer_to_color(color_value)
		record = {
			'barcode': kwargs.get('barcode'),
			'index':   kwargs.get('index'),
			'color':   color,
			'fluor':   channel.get('_Fluor', channel.get("@Fluor")),
			'name':    name,
			'marker':  marker_name,
			'signal':  signal
		}

		result = schemachannel.ChannelDataClass(**record)
		return result

	def get_channel_data_from_text(self, text: str) -> Dict[str, schemachannel.ChannelData]:

		if imagedescription.is_xml(text):
			result = self.get_channel_data_xml(text)
		else:
			result = self.get_channel_data_json(text)

		return result

	def get_channel_data_xml(self, data: Union[str, Path, Dict[str, Any]], **kwargs):
		data = imagedescription.coerce_to_dict(data)
		return self.get_channel_data_json(data, **kwargs)

	def get_channel_data_json(self, data: Union[str, Dict[Union[int, str], schemaome.OMESchema]], **kwargs) -> Dict[str, schemachannel.ChannelData]:
		""" Quick method to get the channel info, since that's usually all we need."""
		data = self._coerce_to_dict(data)
		if "OME" in data:
			data = data["OME"]

		image = data['Image']
		pixels = image['Pixels']
		channels = pixels['Channel']

		barcode = image.get("_Name", image.get("@Name"))

		result = dict()
		for index, channel in enumerate(channels):
			item = self.parse_channel_item(channel, barcode = barcode, index = index)
			if item.marker not in result:  # Used to filter qptiff channels
				result[item.marker] = asdict(item)

		return result

	def get_channel_data_image(self, path: Path, **kwargs):
		descriptions = imagedescription.get_all_descriptions(path)
		description = descriptions[0]['text']
		return self.get_channel_data_xml(description, **kwargs)


def main():
	pass


if __name__ == "__main__":
	main()
