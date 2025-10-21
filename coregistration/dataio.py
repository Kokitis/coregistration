from pathlib import Path
from typing import *
import numpy
import tifffile
from loguru import logger
import numpy

def normalize(array:numpy.ndarray)->numpy.ndarray:
	logger.warning(f"The normalize sunction is not implemented yet.")
	return array
def _coerce_to_image_array(source: Union[str, Path], memmap: bool = False) -> numpy.ndarray:
	"""
		Tries to extract the image data from the given file.
	Parameters
	----------
	source: str | Path
		The source image.
	memmap: bool = False
		Whether to use memory-mapping rather than loading the entire file.

	Returns
	-------
	numpy.ndarray
		The image data.
	"""
	if isinstance(source, str):
		source = Path(source)
	if source.suffix.lower() in {'.tif', '.tiff', '.qptiff'}:
		# Check if the array can fit in memory.
		filesize = source.stat(follow_symlinks = True).st_size / 1024 ** 2  # In MB
		if filesize > 4_000 or memmap:
			try:
				array = tifffile.memmap(source)
			except ValueError as exception:
				message = f"Failed to read the file '{source}' (size = {filesize:.2f}MB) with exception '{exception}'. May still be able to read in the file using imread, but it will require more memory."
				logger.error(message)
				raise ValueError(message)
		else:
			array = tifffile.imread(str(source))
	elif source.suffix == '.npy':
		array = numpy.load(source)
	else:
		message = f"Invalid image file extension: {source}"
		raise ValueError(message)
	return array

def _clip_array(array:List | numpy.ndarray)->numpy.ndarray:
	"""
		Forces the input array to de in the range [0, 1]
	Parameters
	----------
	array: numpy.ndarray.
		The input array

	Returns
	-------
	numpy.ndarray
		The array with the values scaled to be between 0 and 1
	"""
	if not isinstance(array, numpy.ndarray):
		array = numpy.array(array)

	array = array - array.min()
	array = array / array.max()
	return array
def read_array(source: Union[str, Path, numpy.ndarray], norm: bool = False, clip: bool = False, memmap: bool = False) -> numpy.ndarray:
	"""
		Reads a number of different formats representing an array.
	Parameters
	----------
	source: Union[str,Path,numpy.ndarray]
		If the input is an array, this will scale the values to the domain [0,1] and normalize it.
	norm: bool = False
		Whether to normalize the array using percentile-based image normalization
	memmap: bool = False
		Whether to memory-map the input file rather than loading the entire file at once.
	clip: bool = False
		Whether to scale the array values so they are within the range [0, 1]
	"""
	if isinstance(source, numpy.ndarray):
		array = source
	else:
		array = _coerce_to_image_array(source, memmap = memmap)

	if norm:
		array = normalize(array, 1, 99.8, axis = (0, 1))
	elif clip:
		array = _clip_array(array)
	return array

