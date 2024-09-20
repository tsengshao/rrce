import numpy as np
import pandas as pd
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
from netCDF4 import Dataset
from scipy.interpolate import RectBivariateSpline

class data_collector:
    def __init__(self, exp, tIdx):
        self.exp = exp
        self.tIdx  = tIdx 
        self.thNC = Dataset(f'{config.vvmPath}/archive/{self.exp}.L.Thermodynamic-{tIdx:06d}.nc','r')
        self.dyNC = Dataset(f'{config.vvmPath}/archive/{self.exp}.L.Dynamic-{tIdx:06d}.nc','r')
        self.sfNC = Dataset(f'{config.vvmPath}/archive/{self.exp}.C.Surface-{tIdx:06d}.nc','r')
        self.radNC = Dataset(f'{config.vvmPath}/archive/{self.exp}.L.Radiation-{tIdx:06d}.nc','r')
        self.wpNC = Dataset(f'{config.dataPath}/wp/{exp}/wp-{tIdx:06d}.nc','r')
    def get_cwv(self):
        data = self.wpNC.variables['cwv'][0].data
        return {'data':data, 'long_name':'column water vapor', 'units':'kg/m2', 'ndim':'2d'}
    def get_lwp(self):
        data = self.wpNC.variables['lwp'][0].data
        return {'data':data, 'long_name':'liquid water path', 'units':'kg/m2', 'ndim':'2d'}
    def get_iwp(self):
        data = self.wpNC.variables['iwp'][0].data
        return {'data':data, 'long_name':'ice water path', 'units':'kg/m2', 'ndim':'2d'}
    def get_rain(self):
        data = self.sfNC.variables['sprec'][0].data*3600
        return {'data':data, 'long_name':'rain', 'units':'mm/hr', 'ndim':'2d'}
    def get_zeta(self):
        data = self.dyNC.variables['zeta'][0].data
        return {'data':data, 'long_name':'vertical vorticity', 'units':'1/s2', 'ndim':'3d'}


def compute_shortest_distances_vectorized(x_coords, y_coords, x0, y0):
    width = x_coords[-1]-x_coords[0] 
    height = y_coords[-1]-y_coords[0] 
    # Apply periodic boundary conditions
    dx = x_coords - x0
    dy = y_coords[:,np.newaxis] - y0
    dx = (dx + width / 2) % width - width / 2
    dy = (dy + height / 2) % height - height / 2
    distances = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)
    return distances, theta

def convert_uv2rt(u,v,theta):
    u_r  = u*np.cos(theta)+v*np.sin(theta)
    u_th = -u*np.sin(theta)+v*np.cos(theta)
    return u_r, u_th

def convert_rth2xy(r, theta, x0, y0, L_x, L_y):
    y = (r*np.sin(theta) + y0)%(L_x)
    x = (r*np.cos(theta) + x0)%(L_y)
    return x, y

def read_center_file(fname, colname=None):
    # ../../data/find_center/czeta0km_positivemean/RRCE_3km_f00_16.txt
    f = open(fname, 'r')
    data = f.read().split('\n')
    f.close()
    center_info = []
    center_info_flag = False
    idxline = 0
    for i in range(len(data)):
      line = data[i].strip()
      if len(line)==0: continue
      if 'center info' in line:
        center_info_flag = not center_info_flag
        continue
      if center_info_flag:
        center_info.append(line)
        continue
      if 'ts' in line:
        col_name = line.split()
        table    = pd.DataFrame(columns=col_name,dtype=float)
        continue
      table.loc[int(idxline)] = np.array(line.split()).astype(float)
      idxline += 1
    if type(None) != type(colname):
      output = table[colname]
    else:
      output = table
    return center_info, output

def regrid_data_c2p(xc_1d, yc_1d, rawdata, x_polar, y_polar):
  fun = RectBivariateSpline(xc_1d, yc_1d, rawdata.T)
  data_polar = fun(x_polar.flatten(), y_polar.flatten(), grid=False)
  data_polar = data_polar.reshape(x_polar.shape)
  return data_polar
