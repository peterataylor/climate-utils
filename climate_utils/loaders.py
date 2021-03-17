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
    fn_template = _as_template(fn_pattern)

    if known_bounds is not None:
        return bounded_netcdf_loader(fn_template,known_bounds)
    return whole_grid_netcdf_loader(fn_template)

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
    return _first_var(dataset,['lng','longitude','lon'])

def _find_slice(dim_range,dimension_variable):
    data = dimension_variable[...]
    if (max(dim_range) > max(data)) or (min(dim_range) < min(data)):
        raise Exception('Out of bounds. Dimension %s does not cover required range'%dimension_variable.name)

    if data[0] > data[-1]:
        start = np.argmin(dim_range[0]<data)
        end = np.argmax(data<dim_range[1]) -1
        if data[end] > dim_range[1]:
            end -= 1
        step = -1
    else:
        start = np.argmax(data>dim_range[0])
        if data[start] > dim_range[0]:
            start -= 1
        step = 1

        end = np.argmin(dim_range[1]>data)+1
            
    return (start,end,step) 

def _affine_dim(v,slice):
    size = abs(v[1]-v[0])
    return size,slice[0],slice[2]

def _affine_from_nc(x_var,x_slice,y_var,y_slice):
    from affine import Affine
    x_size, x_0, x_step = _affine_dim(x_var,x_slice)
    y_size, y_0, y_step = _affine_dim(y_var,y_slice)

    return Affine(x_step*x_size,0,x_var[x_0],
                  0,y_step*y_size,y_var[y_0])


def bounded_netcdf_loader(fn_template,known_bounds):
    import netCDF4 as nc
    if hasattr(known_bounds,'total_bounds'):
        known_bounds = known_bounds.total_bounds
    min_lon,min_lat,max_lon,max_lat = known_bounds
    lon_range = [min_lon,max_lon]
    lat_range = [min_lat,max_lat]

    def loader(variable,date):
        args = _pattern_substitutions(variable,date)
        fn = fn_template.substitute(**args)

        dataset = nc.Dataset(fn,'r')
        try:
            if hasattr(date,'to_pydatetime'):
                date = date.to_pydatetime()
            if hasattr(date,'to_datetime'):
                date = date.to_datetime()

            ix = nc.date2index(date,_time_var(dataset),select='exact')
            x_var = _x_var(dataset)
            y_var = _y_var(dataset)

            x_slice = _find_slice(lon_range,x_var)
            y_slice = _find_slice(lat_range,y_var)

            y_slice = (y_slice[1]-1,y_slice[0]-1,-y_slice[2])
            if y_slice[1] < 0: y_slice[1] = None
            if y_slice[0] < 0: y_slice[0] = None

            arr = dataset.variables[variable][ix,slice(*y_slice),slice(*x_slice)] 
            affine = _affine_from_nc(x_var,x_slice,y_var,y_slice)

            return arr,affine
        finally:
            dataset.close()
    return loader

def whole_grid_netcdf_loader(fn_template):
    import netCDF4 as nc

    def loader(variable,date):
        args = _pattern_substitutions(variable,date)

        fn = fn_template.substitute(**args)

        dataset = nc.Dataset(fn,'r')
        try:
            ix = nc.date2index(date,_time_var(dataset),select='exact')
            x_var = _x_var(dataset)
            y_var = _y_var(dataset)

            x_slice = _find_slice(sorted(x_var[...][[0,-1]]),x_var)
            y_slice = _find_slice(sorted(y_var[...][[0,-1]]),y_var)

            arr = dataset.variables[variable][ix,slice(*y_slice),slice(*x_slice)] 
            affine = _affine_from_nc(x_var,x_slice,y_var,y_slice)
            return arr,affine
        finally:
            dataset.close()
    return loader
