import datetime
from typing import *

ReferenceLabel = NewType("ReferenceLabel", str)  # Specific format: 'ref{int}'


class FilterSchema(TypedDict):
	Name: str
	Response: str
	Date: datetime.datetime
	FilterID: str


class BandSchema(TypedDict):
	Name: str
	Response: float
	Date: datetime.datetime
	FilterID: str


class BandSchemaV1(TypedDict):
	Cuton: float
	Cutoff: float
	Active: bool
	Name: str  # Ex. "DAPI", ""Opal 570"


class ResponsivitySchema(TypedDict):
	Filter: FilterSchema


class ROISchema(TypedDict):
	X: int
	Y: int
	Width: int
	Height: int


class CameraSettingsSchema(TypedDict):
	Gain: int
	OffsetCounts: int
	Binning: int
	BitDepth: int
	Orientation: str
	ROI: ROISchema


class ScanProfileCameraSettings(TypedDict):
	_ref: ReferenceLabel
	V: int
	Gain: int
	Offset: int
	Bits: int
	Binning: int
	ReadoutSpeed: Literal['Auto']
	ROI: str  # ROI bounding box Ex. "0, 0, 1920, 1440"
	RotateImage: bool
	MirrorImage: bool
	FrameAverageCount: int


class ScanResolutionSchema(TypedDict):
	_ref: ReferenceLabel
	V: int
	PixelSizeMicrons: float
	Magnification: str
	ObjectiveName: str
	Binning: int


class MsiResolutionSchema(ScanResolutionSchema):
	pass


class BandNamesSchema(TypedDict):
	pass


class FixedFilterSchema(TypedDict):
	_ref: str
	V: int
	Manufacturer: str
	PartNumber: str
	Name: str
	TransmissionBands: None


class EmissionFilterSchema(TypedDict):
	_ref: str
	V: int
	FixedFilter: FixedFilterSchema
	Bands: None


class FilterPairSchema(TypedDict):
	_ref: str
	V: int
	FactorDefined: bool
	EmissionFilter: EmissionFilterSchema
	ExcitationFilter: None


class ExcitedFilterPairSchema(TypedDict):
	_ref: str
	V: int
	BandIndex: int
	FilterPair: FilterPairSchema


class ScanBandSchema(TypedDict):
	_ref: str
	_subtype: Literal["SpectralSegmentBasis"]
	V: List[int]
	TunableFilterEngaged: bool
	BandIndex: int
	ExcitedFilterPair: ExcitedFilterPairSchema
	WavelengthGroup: None
	Exposure: None


class ScanBandsISchema(TypedDict):
	_ref: str
	ScanBands_i: List[ScanBandSchema]


class MsiBandsSchema(TypedDict):
	pass


ScanColorTableSchema = TypedDict(
	"ScanColorTableSchema",
	{
		'_ref':             ReferenceLabel,
		'ScanColorTable-k': List[str],
		'ScanColorTable-v': List[str]
	}
)


class BandCollectionSchema(TypedDict):
	Bands: List[BandSchemaV1]


class ExcitationFilterSchema(TypedDict):
	Name: str  # Ex. "DAPI/Opal570/690"
	Manufacturer: str
	PartNo: str
	Bands: BandCollectionSchema


class RootSchema(TypedDict):
	_s_v: int
	_ref: str  # Ex. 'ref0'
	V: int
	OpalKitType: Literal['Opal7Polaris']

	# "DAPI MSI_Semrock:FF01-554/807-25 Emission / Semrock:FF01-387/735-25 Excitation"
	MsiFocusBand: str
	SampleIsTMA: bool
	BarcodeFormats: Literal['NoFormat']
	CoverslipThickness: Literal['Normal']
	CameraSettings: CameraSettingsSchema

	Compression: Literal['LZW']
	JPEGQuality: int  # 0-100
	Mode: Literal['im_Fluorescence']
	Name: str
	ScanResolution: ScanResolutionSchema
	MsiResolution: MsiResolutionSchema
	ScanBands: ScanBandsISchema
	MsiBands: MsiBandsSchema

	# "DAPI_Semrock:FF01-453/571/709-25 Emission / Semrock:FF01-391/538/649-25 Excitation"
	OverviewBand: str
	ScanFocusBand: str
	EnableSaturationProtection: bool
	ScanColorTable: ScanColorTableSchema
	AlgorithmPath: None
	SelectionStrategy: None
	ScanEntireCoverslipRegion: bool


class ScanProfileSchema(TypedDict):
	root: RootSchema


class PerkinsSchema(TypedDict):
	DescriptionVersion: int
	AcquisitionSoftware: str
	ImageType: Literal['FullResolution']
	Identifier: str
	SlideID: str  # Sample Barcode
	ComputerName: str
	IsUnmixedComponent: bool
	ExposureTime: int
	SignalUnits: int
	Name: str  # Ex. DAPI
	Color: str  # Ex. "0,0,255"
	Responsivity: ResponsivitySchema
	Objective: str  # Ex. "10x"
	ExcitationFilter: ExcitationFilterSchema
	EmissionFilter: ExcitationFilterSchema
	CameraSettings: CameraSettingsSchema
	InstrumentType: str
	LampType: str
	CameraType: str
	CameraName: str
	ScanProfile: ScanProfileSchema
	ValidationCode: str
