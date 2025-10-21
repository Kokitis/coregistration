from pathlib import Path
from typing import *

import SimpleITK as sitk
import numpy
from loguru import logger


def resample(fixed: numpy.ndarray, moving: numpy.ndarray, tx: Union[str, Path, sitk.Transform], filename: Path = None,
		compose: bool = False
) -> numpy.ndarray:
	"""
		Transforms the moving channel according to the given transform
	"""
	if isinstance(fixed, numpy.ndarray):
		fixed = sitk.GetImageFromArray(fixed)
	if isinstance(moving, numpy.ndarray):
		moving = sitk.GetImageFromArray(moving)

	if isinstance(tx, (str, Path)):
		tx = sitk.ReadTransform(str(tx))

	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkGaussian)
	resampler.SetDefaultPixelValue(0)
	resampler.SetTransform(tx)

	out = resampler.Execute(moving)
	simg2 = sitk.Cast(sitk.RescaleIntensity(out, 0, 1), sitk.sitkFloat32)
	if filename or compose:
		simg1 = sitk.Cast(sitk.RescaleIntensity(fixed), sitk.sitkUInt8)
		simg2 = sitk.Cast(sitk.RescaleIntensity(out), sitk.sitkUInt8)
		cimg = sitk.Compose(simg1, simg2, simg1 // 2. + simg2 // 2.)
		if filename:
			sitk.WriteImage(cimg, str(filename))
		if compose:
			return cimg

	simg2 = sitk.GetArrayFromImage(simg2)
	return simg2
