import numpy as np
import pandas as pd
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.thermo as thermo
from netCDF4 import Dataset
from scipy.interpolate import RectBivariateSpline
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib as mpl

class data_collector:
    def __init__(self, exp, tIdx, idztop=None):
        self.exp = exp
        self.tIdx  = tIdx 
        self.thNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Thermodynamic-{self.tIdx:06d}.nc','r')
        self.dyNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Dynamic-{self.tIdx:06d}.nc','r')
        self.sfNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.C.Surface-{self.tIdx:06d}.nc','r')
        self.radNC = Dataset(f'{config.vvmPath}/{exp}/archive/{self.exp}.L.Radiation-{self.tIdx:06d}.nc','r')
        self.wpNC = Dataset(f'{config.dataPath}/wp/{exp}/wp-{self.tIdx:06d}.nc','r')
        
        self.var2dlist = ['cwv','iwp','lwp','rain','olr','netLW','netSW', 'sh', 'lh']
        self.var3dlist = ['u', 'v', 'w', 'zeta', 'eta', 'xi', 'divg',\
                          'th', 'qv', 'qc', 'qi', 'qr', 'qvs', 'mse',\
                         ]

        self.setGRIDinfo()
        self.idztop = idztop
        if type(idztop) == type(None): self.idztop = int(nz)
        self.zc = self.zc[:self.idztop]
        self.nz = self.idztop

        self.setBARinfo()

    def setGRIDinfo(self):
        self.xc = self.thNC['xc'][:].data  #meter
        self.yc = self.thNC['yc'][:].data  #meter
        self.zc = self.thNC['zc'][:].data  #meter
        self.nx = self.xc.size
        self.ny = self.yc.size
        self.nz = self.zc.size
        self.dx = np.diff(self.xc)[0]
        self.dy = np.diff(self.yc)[0]

    def setBARinfo(self):
        vvmLoader    = VVMLoader(f"{config.vvmPath}/{self.exp}/", subName=self.exp)
        self.rho3d   = vvmLoader.loadRHO()[:self.idztop][:,np.newaxis,np.newaxis]
        self.pibar3d = vvmLoader.loadPIBAR()[:self.idztop][:,np.newaxis,np.newaxis]
        self.pbar3d  = vvmLoader.loadPBAR()[:self.idztop][:,np.newaxis,np.newaxis]

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

    def get_radial_and_tangential_wind(self, theta_2d, speed_x, speed_y):
        u_3d = self.get_variable('u')['data'] - speed_x
        v_3d = self.get_variable('v')['data'] - speed_y
        radial, tangential = convert_uv2rt(u_3d,v_3d,theta_2d[np.newaxis,:,:])
        radial_dict = {'data':radial, 'long_name':'radial wind', 'units':'m/s', 'dim_type':'3d', 'positive':False}
        tangential_dict = {'data':tangential, 'long_name':'tangential wind', 'units':'m/s', 'dim_type':'3d', 'positive':False}
        return radial_dict, tangential_dict

    def get_variable(self,varn):
      varn_check = varn.lower()
      ## integral qv/qc/qi
      if varn_check == 'cwv':
          data = self.wpNC.variables['cwv'][0].data
          return {'data':data, 'long_name':'column water vapor', 'units':'kg/m2', 'dim_type':'2d', 'positive':True}
      elif varn_check == 'lwp':
          data = self.wpNC.variables['lwp'][0].data
          return {'data':data, 'long_name':'liquid water path', 'units':'kg/m2', 'dim_type':'2d', 'positive':True}
      elif varn_check == 'iwp':
          data = self.wpNC.variables['iwp'][0].data
          return {'data':data, 'long_name':'ice water path', 'units':'kg/m2', 'dim_type':'2d', 'positive':True}
      ## Surface
      elif varn_check == 'rain':
          data = self.sfNC.variables['sprec'][0].data*3600
          return {'data':data, 'long_name':'rain', 'units':'mm/hr', 'dim_type':'2d', 'positive':True}
      elif varn_check == 'sh':
          data = self.sfNC.variables['wth'][0].data*1004 
          return {'data':data, 'long_name':'sensible heat flux', 'units':'W/m2', 'dim_type':'2d', 'positive':False}
      elif varn_check == 'lh':
          data = self.sfNC.variables['wqv'][0].data*2.5e6
          return {'data':data, 'long_name':'latent heat flux', 'units':'W/m2', 'dim_type':'2d', 'positive':False}
      elif varn_check == 'olr':
          data = self.sfNC.variables['olr'][0].data
          return {'data':data, 'long_name':'outgoing longwave radiation', 'units':'W/m2', 'dim_type':'2d', 'positive':True}
      ## Dynamics
      elif varn_check == 'zeta':
          data = self.dyNC.variables['zeta'][0,:self.idztop].data
          return {'data':data, 'long_name':'z-component of vorticity', 'units':'1/s2', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'eta':
          data = self.dyNC.variables['eta'][0,:self.idztop].data
          return {'data':data, 'long_name':'y-component of vorticity', 'units':'1/s2', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'xi':
          data = self.dyNC.variables['xi'][0,:self.idztop].data
          return {'data':data, 'long_name':'x-component of vorticity', 'units':'1/s2', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'u':
          data = self.dyNC.variables['u'][0,:self.idztop].data
          return {'data':data, 'long_name':'zonal velocity', 'units':'m/s', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'v':
          data = self.dyNC.variables['v'][0,:self.idztop].data
          return {'data':data, 'long_name':'meridional velocity', 'units':'m/s', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'w':
          data = self.dyNC.variables['w'][0,:self.idztop].data
          return {'data':data, 'long_name':'vertical velocity', 'units':'m/s', 'dim_type':'3d', 'positive':False}
      elif varn_check == 'divg':
          u = self.dyNC.variables['u'][0,:self.idztop].data
          v = self.dyNC.variables['v'][0,:self.idztop].data
          u_pad = self.extend_3d_data(u)
          v_pad = self.extend_3d_data(v)
          divg_pad  = np.gradient(u_pad, axis=2)/self.dx + \
                      np.gradient(v_pad, axis=1)/self.dy
          divg  = divg_pad[:,1:-1,1:-1]
          return {'data':divg, 'long_name':'horizontial divergence', 'units':'1/s2', 'dim_type':'3d', 'positive':False}
      ## Thermodynamics 
      elif varn_check == 'th':
          data = self.thNC.variables['th'][0,:self.idztop].data
          return {'data':data, 'long_name':'potential temperature', 'units':'K', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'qv':
          data = self.thNC.variables['qv'][0,:self.idztop].data
          return {'data':data, 'long_name':'water vapor mixing ratio', 'units':'kg/kg', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'qc':
          data = self.thNC.variables['qc'][0,:self.idztop].data
          return {'data':data, 'long_name':'cloud water mixing ratio', 'units':'kg/kg', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'qi':
          data = self.thNC.variables['qi'][0,:self.idztop].data
          return {'data':data, 'long_name':'cloud ice mixing ratio', 'units':'kg/kg', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'qr':
          data = self.thNC.variables['qr'][0,:self.idztop].data
          return {'data':data, 'long_name':'rain mixing ratio', 'units':'kg/kg', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'mse':
          data_cpt   = self.thNC.variables['th'][0,:self.idztop].data*self.pibar3d*1004.
          data_lvqv  = self.thNC.variables['qv'][0,:self.idztop].data*2.5e6
          data_gz    = self.zc[:,np.newaxis,np.newaxis]*9.8
          data = (data_cpt + data_lvqv + data_gz)/1004.
          return {'data':data, 'long_name':'moist static temperature', 'units':'K', 'dim_type':'3d', 'positive':True}
      elif varn_check == 'qvs':
          data_t = self.thNC.variables['th'][0,:self.idztop].data*self.pibar3d
          data    = thermo.qv_sat(data_t, self.pbar3d)
          return {'data':data, 'long_name':'saturated water vapor mixing ratio', 'units':'kg/kg', 'dim_type':'3d', 'positive':True}
      ## Radiation
      elif varn_check == 'netlw':
          down_toa = self.radNC.variables['fdlw'][0,-1,:,:].data
          down_suf = self.radNC.variables['fdlw'][0,1,:,:].data
          up_toa   = self.radNC.variables['fulw'][0,-1,:,:].data
          up_suf   = self.radNC.variables['fulw'][0,1,:,:].data
          # positive flux is defined to be upward
          # NetLW = LWsfc - LWtop
          data     = (-down_suf+up_suf) - (-down_toa+up_toa)
          return {'data':data, 'long_name':'column longwave radiative flux convergence', 'units':'W/m2', 'dim_type':'2d', 'positive':False}
      elif varn_check == 'netsw':
          down_toa = self.radNC.variables['fdsw'][0,-1,:,:].data
          down_suf = self.radNC.variables['fdsw'][0,1,:,:].data
          up_toa   = self.radNC.variables['fusw'][0,-1,:,:].data
          up_suf   = self.radNC.variables['fusw'][0,1,:,:].data
          # positive flux is defined to be downward
          # NetSW = SWtop - SWsfc
          data     = (down_toa-up_toa) - (down_suf-up_suf)
          return {'data':data, 'long_name':'column shortwave radiative flux convergence', 'units':'W/m2', 'dim_type':'2d', 'positive':False}

class ncWriter:
    def __init__(self, fname):
        self.fname = fname

    def put_variables(self, varname, data, attrs):
        if 'nc' not in self.__dict__.keys(): 
            print('This ncWriter can not put variables ... ')
            print('...... please create the coordinate first, ncWriter.create_coordinate !!')
            return
        if len(data.shape)==2:
          vardims = ('time', 'theta', 'radius')
          chunks  = (1, data.shape[0], data.shape[1])
        elif len(data.shape)==3:
          vardims = ('time', 'zc', 'theta', 'radius')
          chunks  = (1, 1, data.shape[1], data.shape[2])
        else:
          print('error data input shape, not 2d or 3d')
          return
        var_nc  = self.nc.createVariable(varname, 'f4', vardims,\
                                         compression='zlib', complevel=4,\
                                         fill_value=-999000000,\
                                         chunksizes=chunks,\
                                        )
        for name, value in attrs.items():
            setattr(var_nc, name, value)
        var_nc[:]  = data[np.newaxis,:,:]
        return

    def close_ncfile(self):
        if 'nc' not in self.__dict__.keys(): 
            print('This ncWriter does not have ncfile ... ')
            print('...... please create the coordinate first, ncWriter.create_coordinate !!')
            return
        self.nc.close()
        return
        
       
    def reset_coordinate(self):
        if 'nc' not in self.__dict__.keys(): 
            print('This ncWriter can not reset_coordinate ... ')
            print('...... please create the coordinate first, ncWriter.create_coordinate !!')
            return
        self.nc.close()
        self.__delattr__('nc')
        return

    def create_coordinate(self, t_min, z_zc_m, y_theta_rad, x_radius_m, center_x_grid, center_y_grid):
        if 'nc' in self.__dict__.keys():
            print('This ncWriter already has the coordinate ... ')
            print('...... no create_coordinate !!')
            return 

        outNC = Dataset(self.fname, 'w', format='NETCDF4')
        _ = outNC.createDimension("time", None)
        _ = outNC.createDimension("zc", z_zc_m.size)
        _ = outNC.createDimension("radius", x_radius_m.size)
        _ = outNC.createDimension("theta",  y_theta_rad.size)
        
        # create variables of coordinate
        time_nc = outNC.createVariable('time',   'f8', ('time'),   fill_value=-9.99e6)
        r_nc    = outNC.createVariable('radius', 'f8', ('radius'), fill_value=-9.99e6)
        th_nc   = outNC.createVariable('theta',  'f8', ('theta'),  fill_value=-9.99e6)
        zc_nc   = outNC.createVariable('zc',     'f8', ('zc'),     fill_value=-9.99e6)
        
        # write attributes(units) of coordinate
        time_nc.units    = "minutes since 0001-01-01 00:00:00.0"
        time_nc.calendar = 'gregorian'
        zc_nc.units      = 'm'
        th_nc.units      = 'rad'
        r_nc.units       = 'm'
        outNC.discription    = "axisysmmetric average"
        outNC.center_x_grid  = center_x_grid
        outNC.center_y_grid  = center_y_grid
        outNC.history        = "Created " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # write data of coordinate
        r_nc[:]  = x_radius_m
        th_nc[:] = y_theta_rad
        zc_nc[:] = z_zc_m
        time_nc[:] = t_min   # minutes, follow time_nc.units
        
        self.nc = outNC
        return

    def write_ctl(self,fname,exp,x,y,z,nt,dt):
        dset = f'^./{exp}/axisy-%tm6.nc'
        str_z = ' '.join([f'{z[i]:.3f}' for i in range(z.size)])
        y  = np.linspace(0,1,y.size)*360
        fctl=f"""
 DSET {dset} 
 DTYPE netcdf
 OPTIONS template
 TITLE data in cylindrical coordinate
 UNDEF 99999.
 CACHESIZE  1000000
 XDEF {x.size} LINEAR {x[0]} {x[1]-x[0]}
 YDEF {y.size} LINEAR {y[0]} {y[1]-y[0]}
 ZDEF {z.size} levels {str_z}
 TDEF {nt} LINEAR 01JAN1998 {dt}mn
 VARS 25
   cwv=>cwv     0 t,y,x column_water_vapor
   iwp=>iwp     0 t,y,x ice
   lwp=>lwp     0 t,y,x liquid
   olr=>olr     0 t,y,x olr
   rain=>rain   0 t,y,x rain
   netLW=>netLW 0 t,y,x netLW
   netSW=>netSW 0 t,y,x netSW
   sh=>sh       0 t,y,x sh
   lh=>lh       0 t,y,x lh
   u=>u        {z.size} t,z,y,x  u
   v=>v        {z.size} t,z,y,x  v
   w=>w        {z.size} t,z,y,x  w
   zeta=>zeta  {z.size} t,z,y,x  zeta
   eta=>eta    {z.size} t,z,y,x  eta
   xi=>xi      {z.size} t,z,y,x  xi
   divg=>divg  {z.size} t,z,y,x  divg
   th=>th      {z.size} t,z,y,x  th
   qv=>qv      {z.size} t,z,y,x  qv
   qc=>qc      {z.size} t,z,y,x  qc
   qi=>qi      {z.size} t,z,y,x  qi
   qr=>qr      {z.size} t,z,y,x  qr
   qvs=>qvs    {z.size} t,z,y,x  qvs
   mse=>mse    {z.size} t,z,y,x  mse
   radi_wind=>rwind      {z.size} t,z,y,x  radial wind
   tang_wind=>twind      {z.size} t,z,y,x  tang wind
 ENDVARS
"""
        fout = open(fname,'w')
        fout.write(fctl)
        fout.close()

        return 





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

def regrid_data_c2p(xc_1d, yc_1d, rawdata, x_polar, y_polar, always_positive=False, ens=-1):
  if ens>0:
    data_polar = np.zeros(x_polar.shape)
    ne = ens; nex=int(np.sqrt(ne)); ney=int(np.sqrt(ne))
    if (nex!=ney or type(ens)!=int): 
      print('error, regrid_data_c2p: please input squart available and interger number(ens)')
      return 
    dx = xc_1d[1]-xc_1d[0]
    dy = yc_1d[1]-yc_1d[0]
    L_x = xc_1d.size*dx
    L_y = yc_1d.size*dy

    for i in range(ne):
      ix_shift = (i//nex-nex//2)*dx
      iy_shift = (i%ney-ney//2)*dy
      x_p = (x_polar + ix_shift)%(L_x)
      y_p = (y_polar + iy_shift)%(L_y)
      fun = RectBivariateSpline(xc_1d, yc_1d, rawdata.T)
      data_member = fun(x_p.flatten(), y_p.flatten(), grid=False)
      data_member = data_member.reshape(x_polar.shape)
      if always_positive: data_member = np.where(data_member<0, 0, data_member)
      data_polar  += data_member
    data_polar /= ne
    return data_polar

  elif ens<=0:
    fun = RectBivariateSpline(xc_1d, yc_1d, rawdata.T)
    data_polar = fun(x_polar.flatten(), y_polar.flatten(), grid=False)
    data_polar = data_polar.reshape(x_polar.shape)
    if always_positive: data_polar = np.where(data_polar<0, 0, data_polar)
    return data_polar

def create_nc_copy_dims(fname, src, kick_out_members):
  # src is the netCDF.Dataset
  # fname is the string
  dst = Dataset(fname,'w')
  # copy global attributes all at once via dictionary
  dst.setncatts(src.__dict__)
  # copy dimensions
  for name, dimension in src.dimensions.items():
    if name in kick_out_members: continue
    size=len(dimension)
    dst.createDimension(
      name, (size if not dimension.isunlimited() else None))
  # copy all file data except for the excluded
  for name in src.dimensions.keys():
    if name in kick_out_members: continue
    variable = src.variables[name]
    data  = variable[:]
    x = dst.createVariable(name, variable.datatype, variable.dimensions)
    # copy variable attributes all at once via dictionary
    dst[name].setncatts(src[name].__dict__)
    dst[name][:] = data
  return dst
 
def add_dims_into_nc(dst, varn, var, dims, attrs):
    _ = dst.createDimension(varn, var.size)
    x = dst.createVariable(varn, 'f8', dims, fill_value=-999000000)
    x[:] = var
    x.setncatts(attrs)
    return x

def create_axmean_ctl_from_axisy_ctl(outdir, exp, append_text=''):
    f=open(f'{outdir}/../axisy_{exp}.ctl','r')
    c0 = f.read()
    f.close()
    c0 = c0.replace('axisy',f'axmean{append_text}')
    c0 = c0.replace('t,y,x','t,e,x')
    c0 = c0.replace('t,z,y,x','t,e,z,x')
    c1 = c0.split('\n')
    for i in range(len(c1)):
      if 'YDEF' in c1[i]:
        idx_ydef = i
        break
    c1[idx_ydef] = ' YDEF 1 LINEAR 0 1'
    c1.insert(idx_ydef+1, ' EDEF 2 NAMES mean gamma')
    f=open(f'{outdir}/../axmean{append_text}_{exp}.ctl','w')
    f.write('\n'.join(c1))
    f.close()
    return

def axisy_quick_view(x_polar, y_polar, radius, theta, data_polar,\
                     xc, yc, rawdata, cx, cy, varname,\
                     savefig=False,savedir=None,saveheader=None):

    if savefig:
        if type(savedir)==type(None) or type(saveheader)==type(None):
            print('please input argument of savedir and saveheader')
            return
        os.system(f'mkdir -p {savedir}')

    x_polar = (x_polar)/1000.
    y_polar = (y_polar)/1000.
    xc      = (xc)/1000.
    yc      = (yc)/1000.
    radius  /= 1000.
    cx      /= 1000.
    cy      /= 1000.

            
    ############ quick view
    plt.figure()
    plt.scatter(x_polar,y_polar,c=radius,s=1)
    plt.colorbar()
    plt.title('radius')
    if savefig: plt.savefig(f'{savedir}/{saveheader}_radius.png', dpi=250)
    plt.figure()
    plt.scatter(x_polar,y_polar,c=theta*180/np.pi,s=1)
    plt.colorbar()
    plt.title('theta')
    if savefig: plt.savefig(f'{savedir}/{saveheader}_theta.png', dpi=250)
    
    # draw
    fig = plt.figure()
    bounds = np.arange(-5, 5.1, 1)
    #bounds = np.arange(-5, 5.1, 1)*1e-4
    
    cmap   = plt.cm.jet
    cmap = plt.cm.RdYlBu_r
    
    norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')
    
    c = plt.pcolormesh(xc, yc, rawdata, norm=norm, cmap=cmap)
    cb = plt.colorbar(c)
    plt.scatter(cx, cy,s=10,c=['k'])
    plt.xlabel('x [km]')
    plt.ylabel('y [km]')
    plt.title(varname)
    plt.title('cartesian',loc='left')
    if savefig: plt.savefig(f'{savedir}/{saveheader}_cartesian.png', dpi=250)
    
    plt.figure()
    plt.scatter(x_polar, y_polar, c=data_polar, s=1, cmap=cmap, norm=norm)
    plt.colorbar()
    plt.scatter(cx, cy,s=10,c=['k'])
    plt.xlabel('x [km]')
    plt.ylabel('y [km]')
    plt.title(varname)
    plt.title('polar',loc='left')
    if savefig: plt.savefig(f'{savedir}/{saveheader}_polarxy.png', dpi=250)
    
    plt.figure()
    plt.pcolormesh(radius,theta,data_polar,norm=norm,cmap=cmap)
    plt.ylabel('theta [rad]')
    plt.xlabel('radius[km]')
    plt.colorbar()
    plt.title(varname)
    if savefig: plt.savefig(f'{savedir}/{saveheader}_polar.png', dpi=250)
    if not savefig: plt.show(block=True)
    plt.close('all')

