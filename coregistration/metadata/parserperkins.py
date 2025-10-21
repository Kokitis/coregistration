from pathlib import Path
from typing import *
from dataclasses import asdict
from infotools import colortools
from coregistration.metadata import schemaperkins, parserbase, imagedescription, schemachannel
from loguru import logger
import json


class DescriptionParserPerkins(parserbase.DescriptionParserBase):
	def __init__(self, markermap: Dict[str, str] = None):
		"""

		Parameters
		----------
		markermap: Dict[str,str]
			Maps signal names to marker names. Ex. 'Opal 780' -> 'SOX10'
		"""
		super().__init__()
		self.markermap = markermap if markermap else {}

	def extract_markermap(self, description: str) -> Dict[str, str]:
		"""
			Attempts to map fluorophores to markers.
		Parameters
		----------
		description: str
			The contents of the description tag for the tiff page with the mapping. Usually the first page in the tiff file.

		Returns
		-------
		Dict[str,str]
			Maps fluorophores to marker names. Will be an empty dict if no mapping is present in the description.
		"""

		data = self._coerce_to_dict(description)
		try:
			library_as_json = data['PerkinElmer-QPI-ImageDescription']['ScanProfile']['root']['UnmixingLibrary']['LibraryAsJSON']
			library_as_json = json.loads(library_as_json)
		except KeyError:
			library_as_json = dict()
		if library_as_json:
			result = {item['fluor']: item['marker'] for item in library_as_json['spectra']}
		else:
			result = dict()
		return result

	def parse_scan_table_marker(self, string: str) -> Tuple[str, str]:
		"""
		Examples
		--------
		"Opal 690_Semrock:FF01-453/571/709-25 Emission / Semrock:FF01-391/538/649-25 Excitation"
		Returns
		-------
		Tuple[str,str,str]
			The marker name and signal name.
		"""
		signal_name = string.split('_')[0]
		marker_name = self.markermap.get(signal_name, signal_name)
		return marker_name, signal_name

	def parse_scan_table(self, scan_color_table_k: List[str], scan_color_table_v: List[str], barcode: Optional[str] = None) -> Dict[str, schemachannel.ChannelData]:
		"""
			Extracts channel data using the scan color table within the image description.
		Parameters
		----------
		scan_color_table_k:List[str]
		scan_color_table_v:List[str]
		barcode: Optional[str]
			Should be given, if available.
		"""
		channel_data = dict()
		for index, (scan_color_k, scan_color_v) in enumerate(zip(scan_color_table_k, scan_color_table_v)):
			marker_name, signal_name = self.parse_scan_table_marker(scan_color_k)
			color = colortools.convert_to_hex(scan_color_v)
			channel = {
				'barcode': barcode,
				'color':   color,
				'index':   index,
				'name':    scan_color_k,  # f"{name_corrected}", #+ (f" ({signal})" if signal else ""),
				'marker':  marker_name,
				'signal':  signal_name
			}
			channel = asdict(schemachannel.ChannelDataClass(**channel))
			channel_data[channel['marker']] = channel

		return channel_data

	def get_scan_settings_from_msi(self):
		pass

	def get_channel_data_from_pages(self, pages: Dict[int, str]):
		"""
			Extracts the data for each page from a mapping of page index to page description. Only the first instance of a marker is used if the image is a qptiff image.
		"""
		channel_data = dict()
		for index, page_description in pages.items():
			channel = self.parse_channel_description(page_description, index)
			if channel and channel.marker not in channel_data:
				channel_data[channel.marker] = asdict(channel)
		config = {
			'channels': channel_data,
			'config':   {}
		}
		return config

	def get_channel_data_from_scan_table(self, data: schemaperkins.PerkinsSchema):

		barcode = data.get('SlideID')
		scan_profile = data['ScanProfile']['root']
		scan_color_table = scan_profile['ScanColorTable']
		scan_color_table_k = scan_color_table["ScanColorTable-k"]
		scan_color_table_v = scan_color_table["ScanColorTable-v"]

		channel_data = self.parse_scan_table(scan_color_table_k, scan_color_table_v, barcode)

		scan_resolution = scan_profile['ScanResolution']

		scan_settings = {
			'Objective':       scan_resolution['ObjectiveName'],
			'Magnification':   scan_resolution['Magnification'],
			'PixelSizeMicros': scan_resolution['PixelSizeMicrons'],
			'Compression':     scan_profile['Compression'],
			'Mode':            scan_profile['Mode']
		}

		config = {
			'config':   scan_settings,
			"channels": channel_data
		}

		return config

	def get_channel_data_xml(self, text: str, index: int = None, aschannel: bool = False):
		"""
			Don't have binary data embedded in the file, so just convert to json and parse that
		"""
		data = imagedescription.coerce_to_dict(text)
		return self.get_channel_data_json(data, aschannel = aschannel, index = index)

	def get_channel_data_json(self, data: Union[str, Dict[Union[int, str], schemaperkins.PerkinsSchema]], index: int = None, aschannel: bool = False):
		"""
			Tries to extract channel data from the given input.
		Parameters
		----------
		data: Union[str, Dict[Union[int, str], schemaperkins.PerkinsSchema]]
			This can be in xml or json format, and can contain information for multiple channels.
			If multiple channels are present, will return all channels unless `aschannel` is `True`
		index: int
			Used to assign the correct index to the channel.
		aschannel:bool = False
			Whether to return information for multiple channels, if possible.
		"""

		data = self._coerce_to_dict(data)

		if "PerkinElmer-QPI-ImageDescription" in data:
			data = data["PerkinElmer-QPI-ImageDescription"]

		scan_profile = data.get('ScanProfile')
		if scan_profile is not None:
			scan_profile = scan_profile['root']

		if 'Name' in data and aschannel:
			# We can still get the marker name and color from the data
			channel_data = self.parse_channel_description(data, index)
			channel_data = {channel_data.marker: asdict(channel_data)}
		elif scan_profile and 'ScanColorTable' in scan_profile and not aschannel:
			channel_data = self.get_channel_data_from_scan_table(data)['channels']
		elif all(isinstance(i, int) for i in data.keys()):
			# Contains the channel description for each page in the tiff file.
			channel_data = self.get_channel_data_from_pages(data)

		else:
			# message = 'Currently unsupported format'
			# raise ValueError(message)
			channel_data = None
		return channel_data

	def get_channel_data_image(self, path: Path, **kwargs):
		descriptions = imagedescription.get_all_descriptions(path)
		channel_data = dict()
		for index, description in descriptions.items():
			text = description['text']
			if imagedescription.is_xml(text):
				item_data = self.get_channel_data_xml(text, index = index, aschannel = True)
			elif imagedescription.is_json(text):
				item_data = self.get_channel_data_json(text, index = index, aschannel = True)
			else:
				message = f"Unknown description format within the image file."
				logger.warning(message)
				item_data = None

			# Filter out duplicated channel info
			if item_data:
				item_data = {key: value for key, value in item_data.items() if key not in channel_data}
				channel_data = {**channel_data, **item_data}
		return channel_data

	def parse_channel_description(self, text: Union[str, Dict], index: int = None) -> Optional[schemachannel.ChannelDataClass]:
		# Check if the given data does not represent a signal channel (Usually the first/last channel)
		if isinstance(text, str):
			data = self._coerce_to_dict(text)
		else:
			data = text

		if 'PerkinElmer-QPI-ImageDescription' in data:
			data = data['PerkinElmer-QPI-ImageDescription']

		for key in ["Responsivity", 'ScanProfile']:  # Removed for readablility
			if key in data:
				data.pop(key)
		# Check if the description contains information related to the markers.
		is_valid = any(i in data for i in {'Barcode', 'Name', 'Marker'})
		if not is_valid:
			return None

		for label in ['Name', 'Marker']:
			name = data.get(label)
			if name:
				break
		else:
			return None

		marker_name, signal = schemachannel.process_name(name)
		# name_corrected = correct_marker_label(marker_name)

		record = {
			'barcode': data.get('SlideID'),
			'color':   colortools.rgb_to_hex(data['Color']),
			'index':   index,
			'name':    name,  # f"{name_corrected}", #+ (f" ({signal})" if signal else ""),
			'marker':  marker_name,
			'signal':  signal
		}

		record = schemachannel.ChannelDataClass(**record)
		# if name != name_corrected and name_corrected not in self.base_markers and name != f'{marker_name} ({signal})':
		#	record['alias'] = name

		return record


def main():
	pass


if __name__ == "__main__":
	main()
