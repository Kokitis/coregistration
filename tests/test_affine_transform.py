from coregistration import affinetransform
import pytest

from coregistration.affine import affinetransform


@pytest.fixture
def transform() -> affinetransform.TransformParameters:
	matrix = [
		[0.1, 0.2, 0.3],
		[0.4, 0.5, 0.6]
	]
	return affinetransform.TransformParameters.from_matrix(matrix)


def test_affine_transform_to_list(transform):
	assert transform.to_list() == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]


def test_affine_transform_to_matrix(transform):
	assert transform.to_matrix().tolist() == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_affine_transform_to_parameters(transform):
	result = transform.to_parameters()
	expected = {
		'a': 0.1,
		'b': 0.2,
		'c': 0.4,
		'd': 0.5,
		'xoff': 0.3,
		'yoff': 0.6
	}
	assert result == expected


def test_affine_transform_to_sitk(transform):
	pass


def test_transform_point():
	matrix = [[1, 0, 20], [0, 1, 10]]
	tx = affinetransform.TransformParameters.from_matrix(matrix)

	point = (13, -1)
	expected = (33, 9)

	assert tuple(tx.transform_point(point)) == expected

def test_solve_affine():
	expected_matrix = [[0.5, 0, 13], [0,2,-9]]
	expected_list = expected_matrix[0] + expected_matrix[1]


	points = [(1,1), (13,4), (10,-2)]
	points_transformed = [(13.5, -7), (19.5, -1), (18, -13)]

	solution = affinetransform.solve_affine(points, points_transformed)
	solution = solution.to_list()

	assert pytest.approx(solution) == expected_list

