from dataclasses import dataclass
from coregistration.metadata import imagedescription, parserperkins, parserome, schemachannel

from .tifftags import *


@dataclass
class ScanSettings:
	objective: str
	magnification: str
	units: str
	unitsPerPixelX: float
	unitsPerPixelY: float
	dimensionOrder: Literal["XYCZT"]
	sizeX: int
	sizeY: int
	sizeZ: int
	sizeC: int
	sizeT: int


def get_channel_data(io: Union[str, Path, Dict[str, Any]], **kwargs) -> Union[schemachannel.ChannelData, Dict['str', schemachannel.ChannelData]]:
	data_type = imagedescription.get_data_type(io)
	datatype, data_source, data_format = data_type.split('-')
	parser = parserperkins.DescriptionParserPerkins() if data_source == 'perkins' else parserome.DescriptionParserOME()
	result = parser.get_channel_data(io, **kwargs)

	return result


def convert_tag_dtypes(tag: tifffile.TiffTag | Any):
	"""
		General Tag Data Types:
		- int
		- float
		- str
		- tuple
		- enum 'COMPRESSION'
		- enum 'PHOTOMETRIC'
		- enum 'PLANARCONFIG'
		- enum 'RESUNIT'
		- enum 'SAMPLEFORMAT'
		- flag 'FILETYPE'
	"""

	tagnames = {
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

	# if isinstance(tag, tifffile.TiffTag):
	#	tag = tag.value

	try:
		name = tag.value.name
		value = tag.value.value
	except AttributeError:
		name = None
		value = tag.value

	record_tag = {
		'code':       tag.code,
		'count':      tag.count,
		'dataformat': tag.dataformat,
		'dtype':      tag.dtype,
		'name':       tag.name,
		'value':      tag.value
	}

	record = {
		'tag':   record_tag,
		'field': tagnames.get(tag.code),
		'name':  name,
		'value': value,
		'type':  str(type(tag))
	}

	return record
