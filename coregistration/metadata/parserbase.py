from pathlib import Path
from typing import *
from coregistration.metadata import imagedescription


class DescriptionParserBase:
	def __init__(self, attr_prefix = '_'):
		self.attr_prefix = attr_prefix

	def _coerce_to_dict(self, io):
		return imagedescription.coerce_to_dict(io, attr_prefix = self.attr_prefix)

	def get_unit_scale(self, text: str) -> Optional[float]:
		raise NotImplementedError

	def get_channel_data_image(self, path: Path, **kwargs):
		raise NotImplementedError

	def get_channel_data_xml(self, data, **kwargs):
		raise NotImplementedError

	def get_channel_data_json(self, data, **kwargs):
		raise NotImplementedError

	def get_channel_data(self, data: Union[Path, str, Dict], **kwargs):
		data_description = imagedescription.get_data_type(data)
		data_type, data_source, data_format = data_description.split('-')
		if data_type == 'image':
			channel_data = self.get_channel_data_image(data, **kwargs)
		else:
			if data_format == 'xml':
				channel_data = self.get_channel_data_xml(data, **kwargs)
			else:
				channel_data = self.get_channel_data_json(data, **kwargs)

		return channel_data


def main():
	pass


if __name__ == "__main__":
	main()
