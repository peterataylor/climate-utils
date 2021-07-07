import string
import os
import numpy as np

def _as_template(pattern):
    if isinstance(pattern,string.Template):
        return pattern
    return string.Template(pattern)

def _pattern_substitutions(variable,date):
    return {
        'year':date.year,
        'month':'%02d'%date.month,
        'day':'%02d'%date.day,
        'hour':'%02d'%date.hour,
        'minute':'%02d'%date.minute,
        'variable':variable
    }

def ascii_grid_loader(fn_pattern):
    '''
    Data loader for ASCII grid data
    '''
    fn_template = _as_template(fn_pattern)
    import rasterio
    def loader(variable,date):
        args = _pattern_substitutions(variable,date)
        fn = fn_template.substitute(**args)
        rio = rasterio.open(fn)
        data = rio.read()[0,:,:].astype('d')
        if rasterio.__version__[0]=='0':
            return data,rio.affine
        return data,rio.transform

    return loader
    
def awap_ascii_by_year(base_path,fn_pattern,date_format):
    #fn_pattern='${variable}.${date}${date}.grid',date_format='%Y%m%d'):
    '''
    Data loader AWAP data, stored by year 
    '''
    fn_template = string.Template(fn_pattern)
    import rasterio
    def loader(variable,date):
        date_string = date.strftime(date_format)
        fn_base = fn_template.substitute(variable=variable,date=date_string)
        fn = os.path.join(base_path,str(date.year),fn_base)
        rio = rasterio.open(fn)
        data = rio.read()[0,:,:].astype('d')
        if rasterio.__version__[0]=='0':
            return data,rio.affine
        return data,rio.transform

    return loader

def netcdf_loader(fn_pattern,known_bounds=None):
    import netCDF4 as nc
    fn_template = _as_template(fn_pattern)

    if known_bounds is not None:
        if hasattr(known_bounds,'total_bounds'):
            known_bounds = known_bounds.total_bounds
        min_lon,min_lat,max_lon,max_lat = known_bounds
        lon_range = [min_lon,max_lon]
        lat_range = [min_lat,max_lat]
        find_slice = _find_slice
    else:
        lat_range = None
        lon_range = None

        def find_slice(*args):
            return slice(None)

    def loader(variable,date):
        args = _pattern_substitutions(variable,date)
        fn = fn_template.substitute(**args)

        dataset = nc.Dataset(fn,'r')
        try:
            x_var = _x_var(dataset)
            y_var = _y_var(dataset)

            x_var.set_auto_mask(False)
            y_var.set_auto_mask(False)

            x_slice = find_slice(lon_range,x_var)
            y_slice = find_slice(lat_range,y_var)

            time_var = _time_var(dataset)
            if time_var is None:
                arr = dataset.variables[variable][y_slice,x_slice]
            else:
                ix = _nc_date_index(date,time_var)
                arr = dataset.variables[variable][ix,y_slice,x_slice]
            affine, flip = _affine_from_nc(x_var[x_slice],y_var[y_slice])
            if flip:
                arr = arr[::-1,:]
            return arr,affine
        finally:
            dataset.close()
    return loader

def _first_var(dataset,names):
    for v in names:
        if v in dataset.variables:
            return dataset.variables[v]
    return None

def _time_var(dataset):
    return _first_var(dataset,['time'])

def _y_var(dataset):
    return _first_var(dataset,['lat','latitude','y'])

def _x_var(dataset):
    return _first_var(dataset,['lng','longitude','lon','x'])

def _find_slice(dim_range,dimension_variable):
    data = np.array(dimension_variable)#[...]
    if (max(dim_range) > max(data)) or (min(dim_range) < min(data)):
        raise Exception('Out of bounds. Dimension %s does not cover required range'%dimension_variable.name)

    if data[0] > data[-1]: # Decreasing - ie N-S or E-W orientation
        start = np.argmin(dim_range[0]<data)
        end = np.argmax(data<dim_range[1]) -1
        if data[end] > dim_range[1]:
            end -= 1
        step = -1
    else: # Increasing - ie S-N or W-E orientation
        start = np.argmax(data>dim_range[0])
        if data[start] > dim_range[0]:
            start -= 1
        step = 1

        end = np.argmin(dim_range[1]>data)+1

    if start < 0:
        start = None
    if end < 0:
        end = None
    return slice(start,end,step) 

def _affine_dim(v):
    size = (v[-1]-v[0])/(v.shape[0]-1)
    return size,v[0]-size/2.0

def _affine_from_nc(x_var,y_var):
    from affine import Affine
    x_size, x_0 = _affine_dim(x_var)

    flip = False
    if y_var[1] > y_var[0]:
        y_var = y_var[::-1]
        flip = True
    y_size, y_0 = _affine_dim(y_var)
    return Affine(x_size,0,x_0,
                  0,y_size,y_0),flip

def _nc_date_index(date,nc_time_var):
    import netCDF4 as nc
    if hasattr(date,'to_pydatetime'):
        date = date.to_pydatetime()
    if hasattr(date,'to_datetime'):
        date = date.to_datetime()

    return nc.date2index(date,nc_time_var,select='exact')

# def bounded_netcdf_loader(fn_template,known_bounds):
#     import netCDF4 as nc
#     if hasattr(known_bounds,'total_bounds'):
#         known_bounds = known_bounds.total_bounds
#     min_lon,min_lat,max_lon,max_lat = known_bounds
#     lon_range = [min_lon,max_lon]
#     lat_range = [min_lat,max_lat]

#     def loader(variable,date):
#         args = _pattern_substitutions(variable,date)
#         fn = fn_template.substitute(**args)

#         dataset = nc.Dataset(fn,'r')
#         try:
#             x_var = _x_var(dataset)
#             y_var = _y_var(dataset)

#             x_var.set_auto_mask(False)
#             y_var.set_auto_mask(False)

#             x_slice = _find_slice(lon_range,x_var)
#             y_slice = _find_slice(lat_range,y_var)

#             # y_slice = (y_slice[1]-1,y_slice[0]-1,-y_slice[2])
#             if y_slice[1] < 0: y_slice[1] = None
#             if y_slice[0] < 0: y_slice[0] = None

#             x_slice = slice(*x_slice)
#             y_slice = slice(*y_slice)
#             time_var = _time_var(dataset)
#             if time_var is None:
#                 arr = dataset.variables[variable][y_slice,x_slice] 
#             else:
#                 ix = _nc_date_index(date,time_var)
#                 arr = dataset.variables[variable][ix,y_slice,x_slice] 
#             affine = _affine_from_nc(x_var[x_slice],y_var[y_slice])

#             return arr,affine
#         finally:
#             dataset.close()
#     return loader

# def whole_grid_netcdf_loader(fn_template):
#     import netCDF4 as nc

#     def loader(variable,date):
#         args = _pattern_substitutions(variable,date)
#         fn = fn_template.substitute(**args)

#         dataset = nc.Dataset(fn,'r')
#         try:
#             x_var = _x_var(dataset)
#             y_var = _y_var(dataset)

#             x_var.set_auto_mask(False)
#             y_var.set_auto_mask(False)

#             x_slice = slice(None)
#             y_slice = slice(None)
#             time_var = _time_var(dataset)
#             if time_var is None:
#                 arr = dataset.variables[variable][y_slice,x_slice]
#             else:
#                 ix = _nc_date_index(date,time_var)
#                 arr = dataset.variables[variable][ix,y_slice,x_slice]
#             affine = _affine_from_nc(x_var[x_slice],y_var[y_slice])

#             return arr,affine
#         finally:
#             dataset.close()
#     return loader

