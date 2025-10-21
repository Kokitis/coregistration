from pathlib import Path
from typing import *

import pandas
import roifile
from loguru import logger
from vectratools import resources, schema

GroupbyType = Dict[Tuple[str, str], Dict[str, Any]]
PointType = Tuple[Union[int, float], Union[int, float]]


class ImageInfo(TypedDict):
	# barcode	groupId	patientId	regionId	inspect	panel
	imageId: str
	patientId: str
	groupId: int
	regionId: str
	panelId: str
	imagePath: str


class ImageInfoExtended(ImageInfo):
	channel: Path
	regions: Path
	coordinates: Path


class ImageIOTable:
	""" Reads in a table which specifies which images should be coregistered.
		Table Columns
		-------------
		patientId: str
		group: int
		panel: int
		path: str

		There are a few optional columns that can be added (at least one is required).
		- 'channel' This should be the filename of the image. The DAPI channel will be extracted from the file
		- 'regions': This should be a compressed (zip) file of ImageJ-compatible cell segmentations.
		- 'coordinates': This should be a table with two required columns: 'center:gemetric:x' and 'center:geometric:y'

		Parameters
		----------
		filename: Path
		ignore: Tuple[str,str]
			A list of barcode pairs which should be ignored by ImageIOTable.
	"""

	def __init__(self, filename: Path, ignore: List[Tuple[str, str]] = None):
		if ignore is None:
			ignore = []
		self.maximum_side_length = 2800
		self.index = -1

		# Use a list to keep track of the order to load groups.
		# self.group_ids = sorted(self.groups.keys())

		self.table, self.group_keys = self._read_table(filename)

		self.group_keys = [i for i in self.group_keys if i not in ignore]

	@staticmethod
	def _unpack_keys(df: pandas.DataFrame) -> List[Tuple[str, str]]:
		""" Replace groups with more than two images with multiple groups with only two elements."""
		# groups = df.groupby(by = [schema.ColumnsTableCoregistrationGroups.id_patient, schema.ColumnsTableCoregistrationGroups.id_group])
		groups = df.groupby(by = [schema.ColumnsTableCoregistrationGroups.id_group])
		keys = list()
		for groupId, group in groups:
			first_row = group.iloc[0]
			image_id_reference = first_row[schema.ColumnsTableCoregistrationGroups.barcode]

			for index, row in group.iloc[1:].iterrows():
				image_id_query = row[schema.ColumnsTableCoregistrationGroups.barcode]
				key = (image_id_reference, image_id_query)
				keys.append(key)
		return keys

	def _read_table(self, filename: Path) -> Tuple[pandas.DataFrame, Tuple[str, str]]:
		df = pandas.read_csv(filename, sep = "\t")

		if 'inspect' in df.columns:
			df.loc[:, 'inspect'] = df['inspect'].fillna('N/A')
		# df = df.sort_values(by = ['patientId', 'groupId', 'panelId'])
		# df = df.sort_values(by = ['id:patient', 'id:group', 'id:panel'])
		df = df.sort_values(by = ['id:group', 'id:panel'])
		keys = self._unpack_keys(df)

		# Convert the 'imagePath' field to Path
		df.loc[:, schema.ColumnsTableCoregistrationGroups.image_path] = df[schema.ColumnsTableCoregistrationGroups.image_path].apply(lambda s: Path(s))

		return df.set_index("barcode"), keys

	def get_group(self, index: int = None) -> List[ImageInfo]:
		if index is None:
			index = self.index
		image_ids = list(self.group_keys[index])
		group = self.table.loc[image_ids].reset_index()  # Reset the index else the imageId field will be missing
		# group = group.to_records()
		group = [group.iloc[0].to_dict(), group.iloc[1].to_dict()]
		return group

	@staticmethod
	def get_image_regions(filename: Path) -> roifile.ImagejRoi:
		return roifile.ImagejRoi.fromfile(str(filename))

	@staticmethod
	def get_image_data(filename: Path) -> resources.Image:
		image = resources.Image(filename)
		return image


	def get_slide_data(self, filename: Path) -> resources.Image:
		"""
			Generates a resources.Image object
		"""
		# Select the resolution group which most closely matches a given resolution
		slide = resources.WholeSlide(filename)
		resolution_code = max(1, resources.wholeslide.select_resolution_code(filename, self.maximum_side_length)-1)
		logger.debug(f"{resolution_code=}")
		#resolution_code = slide.select_resolution_code(1872 * 1404)
		image = slide.get_image(resolution_code)
		return image

	@staticmethod
	def get_image_coordinates(filename: Path) -> pandas.DataFrame:
		table = pandas.read_csv(filename, sep = "\t")
		return table['center:geometric:x', 'center:geometric:y']

	def get_image(self, filename: Path) -> resources.Image:
		# Obsolete
		if filename.suffix in {'.tiff', '.qptiff'}:
			#result = self.get_slide_data(filename)
			result = self.get_image_data(filename)
		elif filename.suffix == '.tif':
			result = self.get_image_data(filename)
		elif filename.suffix == '.zip':
			result = self.get_image_regions(filename)
		elif filename.suffix == '.tsv':
			result = self.get_image_coordinates(filename)
		else:
			message = f"Not a valid filetype: {filename.name}"
			raise ValueError(message)
		return result

	def get_next_group(self):
		self.index += 1
		group = self.get_group()
		return group

	def get_previous_group(self):
		self.index -= 1
		group = self.get_group()
		return group
