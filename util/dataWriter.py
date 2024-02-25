import numpy as np
import os, sys
import xarray as xr

class DataWriter:
    def __init__(self, outputPath):
        self.outputPath = outputPath        
        self.checkExistOrCreate(self.outputPath)

    def checkExistOrCreate(self, outputPath):
        if not os.path.exists(outputPath): 
            print("Path is not exist, created")
            os.system('mkdir -p '+outputPath)
        else:
            print("Path exists")

    def toNC(self, fname, data, coords, varName=None, dims=None):
        if dims != None and varName != None:
            xrData = xr.DataArray(data, 
                                  coords = coords,
                                  dims = dims,
                                  name = varName)
        else:
            xrData = xr.Dataset(data, 
                                coords = coords)
        xrData.to_netcdf(self.outputPath + fname)
        
    def toNPY(self, fname, data):
        np.save(self.outputPath + fname, data)
