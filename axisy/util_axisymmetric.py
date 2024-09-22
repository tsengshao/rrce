import numpy as np
import pandas as pd
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
from netCDF4 import Dataset
from scipy.interpolate import RectBivariateSpline

class data_collector:
    def __init__(self, exp, tIdx, idztop=None):
        self.exp = exp
        self.tIdx  = tIdx 
        self.thNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Thermodynamic-{self.tIdx:06d}.nc','r')
        self.dyNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Dynamic-{self.tIdx:06d}.nc','r')
        self.sfNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.C.Surface-{self.tIdx:06d}.nc','r')
        self.radNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Radiation-{self.tIdx:06d}.nc','r')
        self.wpNC = Dataset(f'{config.dataPath}/wp/{exp}/wp-{self.tIdx:06d}.nc','r')
        
        self.var2dlist = ['cwv','iwp','lwp','rain','olr','netLW','netSW', 'sh', 'lw']
        self.var3dlist = ['u', 'v', 'w', 'zeta', 'eta', 'xi', 'divg',\
                          'th', 'qv', 'qc', 'qi', 'qr',\
                         ]

        self.setGRIDinfo()
        self.idztop = idztop
        if type(idztop) == type(None): self.idztop = int(nz)
        self.zc = self.zc[:self.idztop]
        self.nz = self.idztop

    def setGRIDinfo(self):
        self.xc = self.thNC['xc'][:].data  #meter
        self.yc = self.thNC['yc'][:].data  #meter
        self.zc = self.thNC['zc'][:].data  #meter
        self.nx = self.xc.size
        self.ny = self.yc.size
        self.nz = self.zc.size
        self.dx = np.diff(self.xc)[0]
        self.dy = np.diff(self.yc)[0]

    def extend_3d_data(self, var3d):
        dum = np.zeros((self.nz,self.ny+2,self.nx+2))
        dum[:,1:-1,1:-1] = var3d
        dum[:,0,1:-1]    = var3d[:,-1,:]
        dum[:,-1,1:-1]   = var3d[:,0,:]
        dum[:,1:-1,0]    = var3d[:,:,-1]
        dum[:,1:-1,-1]   = var3d[:,:,0]
        dum[:,0,0]    = var3d[:,-1,-1]
        dum[:,0,-1]   = var3d[:,-1,0]
        dum[:,-1,0]   = var3d[:,0,-1]
        dum[:,-1,-1]  = var3d[:,0,0]
        return dum

    def close(self):
        self.thNC.close()
        self.dyNC.close()
        self.sfNC.close()
        self.wpNC.close()
        self.radNC.close()

    def get_radial_and_tangential_wind(self, theta_2d):
        u_3d = self.get_variable('u')['data']
        v_3d = self.get_variable('v')['data']
        radial, tangential = convert_uv2rt(u_3d,v_3d,theta_2d[np.newaxis,:,:])
        radial_dict = {'data':radial, 'long_name':'radial wind', 'units':'m/s', 'ndim':'3d'}
        tangential_dict = {'data':tangential, 'long_name':'tangential wind', 'units':'m/s', 'ndim':'3d'}
        return radial_dict, tangential_dict

    def get_variable(self,varn):
      varn_check = varn.lower()
      ## integral qv/qc/qi
      if varn_check == 'cwv':
          data = self.wpNC.variables['cwv'][0].data
          return {'data':data, 'long_name':'column water vapor', 'units':'kg/m2', 'ndim':'2d'}
      elif varn_check == 'lwp':
          data = self.wpNC.variables['lwp'][0].data
          return {'data':data, 'long_name':'liquid water path', 'units':'kg/m2', 'ndim':'2d'}
      elif varn_check == 'iwp':
          data = self.wpNC.variables['iwp'][0].data
          return {'data':data, 'long_name':'ice water path', 'units':'kg/m2', 'ndim':'2d'}
      ## Surface
      elif varn_check == 'rain':
          data = self.sfNC.variables['sprec'][0].data*3600
          return {'data':data, 'long_name':'rain', 'units':'mm/hr', 'ndim':'2d'}
      elif varn_check == 'sh':
          data = self.sfNC.variables['wth'][0].data*1004 # @1000hPa
          return {'data':data, 'long_name':'sensible heat flux', 'units':'W/m2', 'ndim':'2d'}
      elif varn_check == 'lh':
          data = self.sfNC.variables['wqv'][0].data*2.5e6
          return {'data':data, 'long_name':'latent heat flux', 'units':'W/m2', 'ndim':'2d'}
      elif varn_check == 'olr':
          data = self.sfNC.variables['olr'][0].data
          return {'data':data, 'long_name':'outgoing longwave radiation', 'units':'W/m2', 'ndim':'2d'}
      ## Dynamics
      elif varn_check == 'zeta':
          data = self.dyNC.variables['zeta'][0,:self.idztop].data
          return {'data':data, 'long_name':'z-component of vorticity', 'units':'1/s2', 'ndim':'3d'}
      elif varn_check == 'eta':
          data = self.dyNC.variables['eta'][0,:self.idztop].data
          return {'data':data, 'long_name':'y-component of vorticity', 'units':'1/s2', 'ndim':'3d'}
      elif varn_check == 'xi':
          data = self.dyNC.variables['xi'][0,:self.idztop].data
          return {'data':data, 'long_name':'x-component of vorticity', 'units':'1/s2', 'ndim':'3d'}
      elif varn_check == 'u':
          data = self.dyNC.variables['u'][0,:self.idztop].data
          return {'data':data, 'long_name':'zonal velocity', 'units':'m/s', 'ndim':'3d'}
      elif varn_check == 'v':
          data = self.dyNC.variables['v'][0,:self.idztop].data
          return {'data':data, 'long_name':'meridional velocity', 'units':'m/s', 'ndim':'3d'}
      elif varn_check == 'w':
          data = self.dyNC.variables['w'][0,:self.idztop].data
          return {'data':data, 'long_name':'vertical velocity', 'units':'m/s', 'ndim':'3d'}
      elif varn_check == 'divg':
          u = self.dyNC.variables['u'][0,:self.idztop].data
          v = self.dyNC.variables['v'][0,:self.idztop].data
          u_pad = self.extend_3d_data(u)
          v_pad = self.extend_3d_data(v)
          divg_pad  = np.gradient(u_pad, axis=2)/self.dx + \
                      np.gradient(v_pad, axis=1)/self.dy
          divg  = divg_pad[:,1:-1,1:-1]
          return {'data':divg, 'long_name':'horizontial divergence', 'units':'1/s2', 'ndim':'3d'}
      ## Thermodynamics 
      elif varn_check == 'th':
          data = self.thNC.variables['th'][0,:self.idztop].data
          return {'data':data, 'long_name':'potential temperature', 'units':'K', 'ndim':'3d'}
      elif varn_check == 'qv':
          data = self.thNC.variables['qv'][0,:self.idztop].data
          return {'data':data, 'long_name':'water vapor mixing ratio', 'units':'kg/kg', 'ndim':'3d'}
      elif varn_check == 'qc':
          data = self.thNC.variables['qc'][0,:self.idztop].data
          return {'data':data, 'long_name':'cloud water mixing ratio', 'units':'kg/kg', 'ndim':'3d'}
      elif varn_check == 'qi':
          data = self.thNC.variables['qi'][0,:self.idztop].data
          return {'data':data, 'long_name':'cloud ice mixing ratio', 'units':'kg/kg', 'ndim':'3d'}
      elif varn_check == 'qr':
          data = self.thNC.variables['qr'][0,:self.idztop].data
          return {'data':data, 'long_name':'rain mixing ratio', 'units':'kg/kg', 'ndim':'3d'}
      ## Radiation
      elif varn_check == 'netlw':
          down_toa = self.radNC.variables['fdlw'][0,-1,:,:].data
          down_suf = self.radNC.variables['fdlw'][0,1,:,:].data
          up_toa   = self.radNC.variables['fulw'][0,-1,:,:].data
          up_suf   = self.radNC.variables['fulw'][0,1,:,:].data
          # positive flux is defined to be upward
          # NetLW = LWsfc - LWtop
          data     = (-down_suf+up_suf) - (-down_toa+up_toa)
          return {'data':data, 'long_name':'column longwave radiative flux convergence', 'units':'W/m2', 'ndim':'2d'}
      elif varn_check == 'netsw':
          down_toa = self.radNC.variables['fdsw'][0,-1,:,:].data
          down_suf = self.radNC.variables['fdsw'][0,1,:,:].data
          up_toa   = self.radNC.variables['fusw'][0,-1,:,:].data
          up_suf   = self.radNC.variables['fusw'][0,1,:,:].data
          # positive flux is defined to be downward
          # NetSW = SWtop - SWsfc
          data     = (down_toa-up_toa) - (down_suf-up_suf)
          return {'data':data, 'long_name':'column shortwave radiative flux convergence', 'units':'W/m2', 'ndim':'2d'}



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
