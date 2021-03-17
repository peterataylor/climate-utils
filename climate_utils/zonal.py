'''
Routines for generating catchment climate inputs from gridded data
'''
from __future__ import print_function
import rasterstats
import numpy as np
import pandas as pd
import string
import os
import sys
from .loaders import awap_ascii_by_year, netcdf_loader, ascii_grid_loader

def compute_cell_list_and_weights(ref_affine,affine,weights):
    lng_offset = int(round((affine.c-ref_affine.c)/affine.a))
    lat_offset = int(round((affine.f-ref_affine.f)/affine.e))
    rows,cols=np.where(weights>0)
    weights = weights[rows,cols]
    rows += lat_offset
    cols += lng_offset
    assert len(rows)==len(weights)
    return rows,cols,weights


def compute_weights(catchments,grid,transform,nodata=-99.90000153,percent_cover_scale=1000):
#    Why do I need to specify nodata? 
#    fn = 'D:/Geospatial/ACARP/SILO/Rain/1990/19900101_rai.txt'
#    rio = rasterio.open(fn)
    sample_data = grid
    transform = transform
    stats = rasterstats.zonal_stats(catchments,sample_data,affine=transform,all_touched=True,raster_out=True,
                                    percent_cover_weighting=True,nodata=nodata,percent_cover_scale=percent_cover_scale)
    return [compute_cell_list_and_weights(transform,s['mini_raster_affine'],s['mini_raster_percent_cover']) for s in stats]


def compute_weighted_mean(data,weights):
    return [np.sum(data[w[0],w[1]] * w[2])/np.sum(w[2]) for w in weights]

def compute_catchment_time_series(variable,catchments,time_period,data_loader,name_attribute='name',
                                  column_naming='${catchment}_${variable}',show_progress=True,
                                  percent_cover_scale=1000):
    '''
    Build a dataframe of catchment average climate data


    '''
    template = string.Template(column_naming)
    name_for = lambda x: template.substitute(catchment=x,variable=variable)
    all_ts = {name_for(sc):[] for sc in catchments[name_attribute]}
    weights = None
    for ts in time_period:
        if show_progress and ts.day==1:
            if ts.month==1:
                print('\n%d'%ts.year,end=' ')
            print(ts.month,end=' ')
            sys.stdout.flush()
        last_day = ts.day
        resp = data_loader(variable,ts)
        if resp is None:
            for i,sc in enumerate(catchments[name_attribute]):
                all_ts[name_for(sc)].append(np.nan)
            continue
        data,transform = resp

        if not weights:
            weights = compute_weights(catchments,data,transform,percent_cover_scale=percent_cover_scale)
        weighted = compute_weighted_mean(data,weights)
        for i,sc in enumerate(catchments[name_attribute]):
            all_ts[name_for(sc)].append(weighted[i])

    return pd.DataFrame(all_ts,index=time_period)
