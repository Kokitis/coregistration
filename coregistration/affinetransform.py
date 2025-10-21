import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import *


import numpy
import pandas
from loguru import logger

PointType = Tuple[Union[int, float], Union[int, float]]
TransformTupleType = Tuple[float, float, float, float, float, float]

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