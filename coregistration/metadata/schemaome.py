import datetime
from typing import *

AnnotationLabelType = NewType('AnnotationLabel', str)
IDLabelType = NewType("IDLabelType", str)  # Specific format: '{Name}:{int}'
"""
	Reference to another part of the spec. The `_id` attribute is usually formatted as '{Object Name}:{Index}'.
	Example
	-------
	{
		"@ID": "Instrument:0"
	}
"""


class BaseSchema(TypedDict):
	_ID: IDLabelType


class AnnotationRefSchema(TypedDict):
	_ID: IDLabelType


class TagSchema(BaseSchema):
	Description: str
	Value: str


class ChannelSchema(BaseSchema):
	_Color: int
	_Fluor: str
	_Name: str
	_SamplesPerPixel: int
	AnnotationRef: List[AnnotationLabelType]


class PlaneSchema(TypedDict):
	_ExposureTime: int
	_ExposureTimeUnit: str
	_TheC: int
	_TheT: int
	_TheZ: int


class TiffDataSchema(TypedDict):
	_FirstC: int
	_FirstT: int
	_FirstZ: int
	_IFD: int


class PixelSchema(TypedDict):
	_BigEndian: bool
	_DimensionOrder: Literal['XYCZT']
	_ID: AnnotationLabelType
	_PhysicalSizeX: float  # Essentially the scale factor in the x direction from pixels to um. Ex. 0.39874 -> ~2.5 px per um.
	_PhysicalSizeXUnit: str  # Actual unit name
	_PhysicalSizeY: float  # Essentially the scale factor in the x direction from pixels to um. Ex. 0.39874 -> ~2.5 px per um.
	_PhysicalSizeYUnit: str
	_SignificantBits: int  # Ex. 16

	_SizeC: int
	_SizeT: int
	_SizeX: int
	_SizeY: int
	_SizeZ: int
	_Type: str  # I think this is the actual pixel value dtype. ex 'unit16'

	Channel: List[ChannelSchema]
	Plane: List[PlaneSchema]
	TiffData: List[TiffDataSchema]
	ROIRef: List[AnnotationRefSchema]


class MicroscopeSchema(TypedDict):
	_Manufacturer: str
	_Model: str


class PlateSchema(TypedDict):
	_ID: AnnotationLabelType
	_Columns: int
	_Rows: int


class ImageSchema(TypedDict):
	_ID: AnnotationLabelType
	_Name: str
	AcquisitionDate: datetime.datetime
	AnnotationRef: List[AnnotationRefSchema]
	InstrumentRef: AnnotationRefSchema
	ROIRef: List[AnnotationRefSchema]
	Pixels: PixelSchema
	Description: str  # This is only present in legacy (custom) descriptions and is a json-formatted string.


class InstrumentSchema(TypedDict):
	_ID: AnnotationLabelType
	AnnotationRef: AnnotationRefSchema
	Microscope: MicroscopeSchema


class EllipseSchema(TypedDict):
	_ID: AnnotationLabelType
	_RadiusX: float
	_RadiusY: float
	_X: float
	_Y: float


class LabelSchema(TypedDict):
	_ID: AnnotationLabelType
	_FontFamily: str
	_FontSize: str
	_FontSizeUnit: str
	_FontStyle: str
	_StrokeColor: str
	_Text: str
	_X: int
	_Y: int


class UnionSchema(TypedDict):
	Ellipse: EllipseSchema
	Label: LabelSchema


class ROISchema(TypedDict):
	_ID: AnnotationLabelType
	AnnotationRef: AnnotationRefSchema
	Union: UnionSchema


class ReagentSchema(TypedDict):
	_ID: AnnotationLabelType
	_ReagentIdentifier: str


class ScreenSchema(TypedDict):
	_ID: AnnotationLabelType
	PlateRef: AnnotationRefSchema
	ReagentIdentifier: str


class XMLAnnotationSchema(TagSchema):
	pass


class StructuredAnnotationSchema(TypedDict):
	CommentAnnotation: List[TagSchema]
	TimestampAnnotation: List[TagSchema]
	XMLAnnotation: List[XMLAnnotationSchema]


class OMESchema(TypedDict):
	_Creator: str
	_xmlns: str
	_xmlns_xsi: str  # Actual key: '@xmlns:xsi'
	_xmlns_schemaLocation: str  # Actual key: '@xmlns:schemaLocation'
	Image: ImageSchema
	Instrument: InstrumentSchema
	Plate: PlateSchema
	ROI: List[ROISchema]
	StructuredAnnotations: StructuredAnnotationSchema
