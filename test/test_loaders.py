from numpy.core.numeric import full
import pytest
from affine import Affine
from climate_utils.loaders import ascii_grid_loader, netcdf_loader, xarray_loader
from datetime import datetime
import os
import gdal
import pandas as pd

TEST_POINTS=[
  ((-23.14,145.85),36.647159576416016),
  ((-19.51,144.22),40.0081901550293),
  ((-22.82,147.39),47.050289154052734),
  ((-22.51,146.31),37.71641159057617)
]

XA_TEST_POINTS=[
  ((-28.229,151.034),0.019999999552965164),#0.02),#0.01999),
  ((-30.45,150.21),0.029999999329447746),#0.03),#0.0299999),
  ((-30.6884,152.3086),0.029999999329447746),#0.03),#0.02999),
]

TEST_BOUNDS=(
  144.0, # min_lon,
  -24.0, # min_lat,
  148.0, # max_lon,
  -18.0, # max_lat
)

NC_FILES=[
  'rescaled.nc',
  'rescaled_flipped.nc'
]

ASC_FILES=[
  'rescaled.asc'
]

DATA_BAND='Band1'
DUMMY_DATE=datetime(2021,7,14,18,0,0)

UNBOUNDED_TESTS=NC_FILES+ASC_FILES

@pytest.mark.parametrize('fn',UNBOUNDED_TESTS)
def test_unbounded(fn:str):
  if fn.endswith('.asc'):
    loader_factory = ascii_grid_loader
  else:
    loader_factory = netcdf_loader
  fn = full_fn(fn)
  assert os.path.exists(fn)
  loader = loader_factory(fn)
  data, affine = loader(DATA_BAND,DUMMY_DATE)
  assert data.shape[0] == 138
  assert data.shape[1] == 177

  check_vals(data,affine)

@pytest.mark.parametrize('fn',NC_FILES)
def test_bounded(fn:str):
  fn = full_fn(fn)
  assert os.path.exists(fn)
  loader = netcdf_loader(fn,TEST_BOUNDS)
  data, affine = loader(DATA_BAND,DUMMY_DATE)

  assert data.shape[0] < 30
  assert data.shape[1] < 20

  check_vals(data,affine)

def full_fn(fn:str)->str:
  return os.path.abspath(
    os.path.join(
      os.path.dirname(__file__),
      '..',
      'test_data',
      fn))

def check_vals(data,affine,points=TEST_POINTS):
  inv_a = Affine.from_gdal(*gdal.InvGeoTransform(affine.to_gdal()))

  for (coords,val) in points:
    [col_f,row_f] = inv_a*coords[::-1]
    [col,row] = [int(col_f),int(row_f)]

    assert data[row,col]==val

def test_xa():
  loader, time_period = xarray_loader(full_fn('data.00*.nc'))

  assert len(time_period)==5
  assert time_period[0].year==2021
  assert time_period[0].month==7
  assert time_period[0].day==14
  assert time_period[0].hour==18

  data, affine = loader('accum_evap',DUMMY_DATE)
  check_vals(data,affine,XA_TEST_POINTS)

