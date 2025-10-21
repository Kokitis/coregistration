from typing import *
from dataclasses import dataclass, asdict
from coregistration import utilities
from infotools import colortools
import re

BASIC_MARKERS = {'DAPI', 'Autofluorescence'}


class ChannelData(TypedDict):
	barcode: Optional[str]  # May not be retrievable from certain images depending on where/how they were generated.
	color: str
	index: int
	name: str
	marker: str
	signal: str
	alias: None | str | List[str]
	fluor: Optional[str]


@dataclass
class ChannelDataClass:
	barcode: str  # May not be retrievable from certain images depending on where/how they were generated.
	color: str
	name: str
	marker: str
	index: Optional[int] = None
	signal: Optional[str] = None
	alias: Optional[str] = None
	fluor: Optional[str] = None

	def __post_init__(self):
		self.color = colortools.convert_to_hex(self.color)
		name_corrected = correct_marker_label(self.marker)
		# logger.debug(f"{self.marker=}\t{name_corrected=}")
		if self.marker != name_corrected:
			self.alias = self.marker
			self.marker = name_corrected

		if self.signal in BASIC_MARKERS or self.signal == self.alias:
			self.signal = None

	def asdict(self) -> ChannelData:
		return asdict(self)


def correct_marker_label(label: str) -> str:
	""" Applies a couple common corrections to ensure descriptions from separate files are consistently formatted (ex 'SOX10+' -> 'SOX10'})"""

	# if ' ' in label and 'Opal' not in label:
	#	label = label.split(' ')[0].strip()
	# remove '+' character
	label = label.replace('+', '')
	# Remove labels formatted as 'DAPI (DAPI)'
	# TODO: Move this to a config file
	aliases = {
		'AF':        'Autofluorescence',
		'Sample':    'Autofluorescence',
		'Sample AF': 'Autofluorescence',
		#'PD1':       'PD-1',
		#'PDL1':      'PD-L1',
		#'HIF1':      "HiF-1",
		#'Ki67':      'Ki-67',
		#'CA9':       'CAIX',
		'Dapi':      'DAPI',
		'FITC':      'DAPI'
	}
	label = aliases.get(label, label)
	for key, replacement in aliases.items():
		label = label.replace(key, replacement)

	# Check for cases where the marker name is given twice, as both a marker and a signal.
	if '(' in label:
		prefix = label.split(' ')[0]
		suffix = label.split(' ')[-1][1:-1]

		if prefix == suffix:
			label = prefix

	return label


def process_name(name: str) -> Tuple[str, str]:
	"""
		Extracts the marker name and signal name from the raw label.
	"""

	pattern_marker = "[-A-Za-z0-9+\s]+"
	pattern_signal = "Opal [\d]+"

	if '/' in name and 'Opal' not in name:
		# Usually formatted as {name}/{signal}
		label_marker_match, label_signal_match = name.split('/')
	else:
		label_marker_match = re.search(pattern_marker, name)
		label_signal_match = re.search(pattern_signal, name)

		if label_signal_match:
			label_signal_match = label_signal_match.group(0)

		if label_marker_match:
			label_marker_match = label_marker_match.group(0).strip()
			if label_marker_match == 'O':
				label_marker_match = label_signal_match
		# If only the signal is present in the label, it will return a 'O' as the result.

		else:
			label_marker_match = label_signal_match

		# Make sure the marker name isn't 'Opal'
		if label_marker_match == 'Opal':
			label_marker_match = name

	return label_marker_match, label_signal_match


def main():
	pass


if __name__ == "__main__":
	main()
