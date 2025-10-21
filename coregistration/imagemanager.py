from pathlib import Path
from typing import *
import pandas
from dataclasses import dataclass

@dataclass
class ImagePair:
	id_group: Any
	barcode_reference: str
	barcode_query: str
	path_reference: Path
	path_query: Path

class ImageManager:
	def __init__(self, path:Path):

		self.groups = self.read_table(path)
		self.index = 0

	def modify_index(self, amount:int)->int:
		self.index += amount
		if self.index < 0:
			self.index = 0
		elif self.index >= len(self.groups):
			self.index = len(self.groups) - 1
		return self.index

	def get_current_barcodes(self)->Tuple[str, str]:
		pair = self.get_group(self.index)
		return (pair.barcode_reference, pair.barcode_query)

	def get_group(self, index:int = None)->ImagePair:
		if index is None:
			index = self.index
		return self.groups[index]

	def get_next_group(self)->ImagePair:
		index = self.modify_index(1)
		return self.groups[index]

	def get_previous_group(self)->ImagePair:
		index = self.modify_index(-1)
		return self.groups[index]



	@staticmethod
	def read_table(path:Path)->List[ImagePair]:
		df = pandas.read_csv(path, sep = "\t")

		groups = df.groupby(by = 'id:group')
		records = list()
		for id_group, group in groups:
			reference = group.iloc[0]

			for index, row in group.iloc[1:].iterrows():
				pair = ImagePair(
					id_group = id_group,
					barcode_reference = reference['barcode'],
					barcode_query = row['barcode'],
					path_reference = reference['path'],
					path_query = row['path'],
				)
				records.append(pair)

		return records


def main():
	from pprint import pprint
	path = Path("/media/proginoskes/storage/proginoskes/Documents/projects/HCC-CBS-231-Hillman-JLuke-PDO-immune/data/PilotExpt-100125/debug/coregistration.tsv")
	manager = ImageManager(path)
	pprint(manager.groups)


if __name__ == "__main__":
	main()
