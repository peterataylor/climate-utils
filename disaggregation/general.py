import pandas as pd
import numpy as np

DEFAULT_THRESHOLD=15
DEFAULT_R_BINS=[0.042] + [0.075+0.05*i for i in range(19)] + [1.0]
DEFAULT_HOURLY_PATTERNS = {1:[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
                   2:[2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   3:[3, 2, 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   4:[6, 5, 4, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   5:[6, 5, 4, 2, 1, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   6:[6, 5, 4, 3, 2, 1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   7:[9, 8, 7, 6, 5, 4, 1, 2, 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   8:[9, 8, 7, 6, 5, 4, 2, 1, 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   9:[9, 8, 7, 6, 5, 4, 3, 2, 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   10:[12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   11:[12, 11, 10, 9, 8, 7, 6, 5, 4, 2, 1, 3, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   12:[12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   13:[15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   14:[15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 2, 1, 3, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   15:[15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                   16:[18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3, 19, 20, 21, 22, 23, 24], 
                   17:[18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 2, 1, 3, 19, 20, 21, 22, 23, 24], 
                   18:[18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 19, 20, 21, 22, 23, 24], 
                   19:[21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3, 22, 23, 24], 
                   20:[21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 2, 1, 3, 22, 23, 24], 
                   21:[21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 22, 23, 24], 
                   22:[24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3], 
                   23:[24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 2, 1, 3],
                   24:[24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]}

class PluvioModel(object):
    def __init__(self,r_cf,max_hour_cf,hourly_distribution,r_bins,hourly_patterns):
        self.r_cf = r_cf
        self.r_bins = r_bins
        self.max_hour_cf = max_hour_cf
        self.hourly_distribution = hourly_distribution
        self.hourly_patterns = hourly_patterns

    def disaggregate(self,total,timesteps=24):
        r_bin = self.r_cf.index.get_loc((self.r_cf>np.random.uniform()).argmax())
        r = (self.r_bins[r_bin] + self.r_bins[r_bin+1])/2.0

        dist = total * np.array(self.hourly_distribution[self.hourly_distribution.columns[r_bin]])

        hr_of_max = (np.random.uniform()<self.max_hour_cf).argmax()
        pattern = np.array(self.hourly_patterns[hr_of_max+1])-1
        return dist[pattern].reshape(timesteps,24//timesteps).sum(axis=1)

def load_pluvio(fn):
    widths=[12,4,2,2]+[7]*240
    timestamp = lambda i:'%02d:%02d'%(i//10,6*(i%10))
    names = ['site','year','month','day']+[timestamp(i) for i in range(240)]
    missing=9999
    return pd.read_fwf(fn,widths=widths,names=names,skiprows=2,na_values=[9999]).dropna()

def pluvio_to_hourly(pluvio):
    just_vals = pluvio[pluvio.columns[4:]]
    hours=['%02d'%hr for hr in range(24)]
    hourly = {}
    for hr in hours:
        tmp = just_vals[[col for col in just_vals.columns if col.startswith(hr)]]
        hourly[hr] = tmp.sum(axis=1)

    return pd.DataFrame(hourly)

def summarise_hourly(hourly_data,rainfall_threshold=DEFAULT_THRESHOLD,r_bins=DEFAULT_R_BINS):
    row_sums = hourly_data.sum(axis=1)
    filtered_vals = hourly_data[row_sums>rainfall_threshold]
    filtered_sums = filtered_vals.sum(axis=1)
    filtered_max = filtered_vals.max(axis=1)
    R = filtered_max / filtered_sums
    max_hour = np.array(filtered_vals).argmax(axis=1)
    
    r_cumul_freq = (R.groupby(pd.cut(R,r_bins)).count()/len(R)).cumsum()

    hour_bins = -0.5 + np.arange(25)
    max_hour_cumul_freq = (np.histogram(max_hour,hour_bins)[0]/len(max_hour)).cumsum()
    return R,max_hour,r_cumul_freq,max_hour_cumul_freq,filtered_vals

def distribute_rainfall(hourly_data,R,r_bins=DEFAULT_R_BINS):
    dist={}
    all_fracs = (hourly_data.transpose()/hourly_data.sum(axis=1)).transpose()
    for i in range(len(r_bins)-1):
        bin_data = np.array(all_fracs[(R>r_bins[i])&(R<=r_bins[i+1])])
        bin_data.sort(axis=1)
        bin_data = bin_data[:,::-1]
        
        if len(bin_data):
            bin_dist = bin_data.mean(axis=0)
            assert abs(1.0-bin_dist.sum())<1e-10
        else:
            bin_dist = [0]*24
        
        dist[(r_bins[i],r_bins[i+1])]=bin_dist
    return pd.DataFrame(dist)

def fit(fn=None,data_frame=None,threshold=DEFAULT_THRESHOLD,r_bins=DEFAULT_R_BINS,hourly_patterns=DEFAULT_HOURLY_PATTERNS):
    if fn:
        data_frame = load_pluvio(fn)
    hourly = pluvio_to_hourly(data_frame)
    R,max_hour,r_cf,max_hour_cf,filtered = summarise_hourly(hourly,threshold,r_bins)
    hourly_distribution = distribute_rainfall(filtered,R,r_bins)

    return PluvioModel(r_cf,max_hour_cf,hourly_distribution,r_bins,hourly_patterns)

