import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import *


import numpy
import pandas
from loguru import logger

PointType = Tuple[Union[int, float], Union[int, float]]
TransformTupleType = Tuple[float, float, float, float, float, float]


@dataclass
class TransformParameters:
	# Can convert between formats.
	matrix: numpy.ndarray

	def __str__(self):
		values = ", ".join([f"{i:.2f}" for i in self.to_list()])
		string = f"TransformParameters({values})"
		return string

	@classmethod
	def from_matrix(cls, matrix: numpy.ndarray) -> 'TransformParameters':
		""" This should be the complete matrix."""
		if len(matrix) == 6:
			matrix = numpy.array(
				[
					matrix[:3],
					matrix[3:6],
					[0, 0, 1]
				]
			)
		return cls(matrix)

	@classmethod
	def from_parameters(cls, parameters: Dict[str, float]) -> 'TransformParameters':
		matrix = [
			[parameters['a'], parameters['b'], parameters['xoff']],
			[parameters['c'], parameters['d'], parameters['yoff']],
			[0, 0, 1]
		]

		matrix = numpy.array(matrix)

		return cls(matrix)

	@classmethod
	def from_sitk(cls, path: Union[str, Path]) -> 'TransformParameters':
		lines = path.read_text().split('\n')
		line = lines[3].strip().split(' ')
		parameters = [float(i) for i in line[1:]]
		a, b, c, d, x_off, y_off = parameters

		matrix = [
			[a, b, x_off],
			[c, d, y_off],
			[0, 0, 1]
		]
		matrix = numpy.ndarray(matrix)
		return cls.from_matrix(matrix)

	def to_matrix(self) -> numpy.ndarray:
		return self.matrix

	def to_parameters(self) -> Dict[str, float]:
		p = {
			'a':    self.matrix[0, 0],
			'b':    self.matrix[0, 1],
			'xoff': self.matrix[0, 2],
			'c':    self.matrix[1, 0],
			'd':    self.matrix[1, 1],
			'yoff': self.matrix[1, 2]
		}

		return p

	def to_list(self) -> List[float]:
		return [self.matrix[0, 0], self.matrix[0, 1], self.matrix[0, 2], self.matrix[1, 0], self.matrix[1, 1],
			self.matrix[1, 2]]

	def to_sitk(self, filename: Path = None) -> Any:
		import SimpleITK as sitk
		parameters = [
			self.matrix[0, 0], self.matrix[0, 1], self.matrix[1, 0],
			self.matrix[1, 1], self.matrix[0, 2], self.matrix[1, 2]
		]
		transform = sitk.AffineTransform(2)
		transform.SetParameters(parameters)
		if filename:
			sitk.WriteTransform(transform, str(filename))
		return transform

	def transform_point(self, point: PointType) -> numpy.ndarray:
		array = numpy.array([point[0], point[1], 1])
		return numpy.dot(self.matrix, array)

	def TransformPoint(self, point) -> numpy.ndarray:
		return self.transform_point(point)


def _coerce_to_array(item) -> numpy.ndarray:
	if isinstance(item, pandas.DataFrame):
		result = item.values
	elif isinstance(item, list):
		result = numpy.array(item)
	else:
		result = item
	return result
def matrix_multiplication(left: numpy.ndarray, right: numpy.ndarray) -> numpy.ndarray:
	"""
		Multiplies the input matrices together
	"""
	# Check if the matrices are compatible.
	if left.shape[1] != right.shape[0]:
		message = f"Invalid matrix dimentions for multiplication: {left.shape=}\t{right.shape=}"
		raise ValueError(message)
	return left @ right

def format_coordinates(coordinates: List[PointType] | numpy.ndarray) -> numpy.ndarray:
	if not isinstance(coordinates, numpy.ndarray):
		coordinates = numpy.array(coordinates)
	z_axis = numpy.ones((coordinates.shape[0], 1))
	result = numpy.concatenate((coordinates, z_axis), axis = 1)

	return result.transpose()

def build_point_array(coordinates: Iterable[PointType]) -> numpy.ndarray:
	""" Creates the matrix containing the mapped points (x -> x'). The result is a [2*n, 6] matrix."""
	sample_points = list()

	for point in coordinates:
		top = [point[0], point[1], 1, 0, 0, 0]
		bottom = [0, 0, 0, point[0], point[1], 1]

		sample_points.append(top)
		sample_points.append(bottom)

	sample_points = numpy.array(sample_points)
	return sample_points


def build_prime_array(coordinates: numpy.ndarray) -> numpy.ndarray:
	prime = coordinates.reshape(2 * len(coordinates), 1)
	return prime


def solve_affine(coordinates_left: numpy.ndarray, coordinates_right: numpy.ndarray) -> numpy.ndarray:
	coordinates_left = _coerce_to_array(coordinates_left)
	coordinates_right = _coerce_to_array(coordinates_right)

	sample_points = build_point_array(coordinates_left)
	prime = build_prime_array(coordinates_right)
	try:
		A = numpy.dot(numpy.linalg.pinv(sample_points), prime)
	except ValueError as exception:
		message1 = f"Could not calculate transform due to mismatched dimensions."
		message2 = f"Shape of Sample Points: {sample_points.shape}"
		message3 = f"Shape of Prime Array: {prime.shape}"

		logger.error(message1)
		logger.error(message2)
		logger.error(message3)

		raise exception

	values = list(itertools.chain.from_iterable(A))
	values = [(float(value) if abs(value) > 1E-3 else 0) for value in values]

	matrix = numpy.array([values[:3], values[3:6], [0, 0, 1]])

	#result = TransformParameters.from_matrix(matrix)
	return matrix

def apply_transform(matrix: numpy.ndarray, coordinates: numpy.ndarray, dropz: bool = True) -> numpy.ndarray:
	"""
		Transforms a coordinate array using the given affine transform
		Parameters
		----------
		matrix: numpy.ndarray
			The affine transformation matrix
		coordinates: numpy.ndarray
			The coordinates to transform
		dropz:bool = True
			When True, the z axis of the transformed array will be dropped.
	"""
	# Check if the input coordinate array already includes the third (z) column.

	coordinates_other = format_coordinates(coordinates)
	result = matrix_multiplication(matrix, coordinates_other)

	# Convert back to an mxn array, where each row representats a single point.
	result = result.transpose()

	# Remove the z column
	if dropz:
		result = result[:, :2]

	return result