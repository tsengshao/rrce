import os, sys
import numpy as np
from netCDF4 import Dataset
sys.path.insert(0, "../")

class VVMLoader:
    def __init__(self, dataDir, subName="exp"):
        self.dataDir = dataDir
        self.subName = subName
        self.headLineIdxOfZZ = self.findheadLineIdx('ZZ(K)')
        self.headLineIdxOfRho = self.findheadLineIdx('RHO(K)')
        self.headLineIdxOfRhoz = self.findheadLineIdx('RHOZ(K)')

    def loadThermoDynamic(self, tIdx):
        fileDir = self.dataDir + "archive/{SN}.L.Thermodynamic-{tIdx:06d}.nc".format(SN=self.subName, tIdx=tIdx)
        return Dataset(fileDir)

    def loadDynamic(self, tIdx):
        fileDir = self.dataDir + "archive/{SN}.L.Dynamic-{tIdx:06d}.nc".format(SN=self.subName, tIdx=tIdx)
        return Dataset(fileDir)

    def loadSurface(self, tIdx):
        fileDir = self.dataDir + "archive/{SN}.C.Surface-{tIdx:06d}.nc".format(SN=self.subName, tIdx=tIdx)
        return Dataset(fileDir)

    def loadRadiation(self, tIdx):
        fileDir = self.dataDir + "archive/{SN}.L.Radiation-{tIdx:06d}.nc".format(SN=self.subName, tIdx=tIdx)
        return Dataset(fileDir)

    def loadZZ(self):
        zz = []
        #with open(self.dataDir + "fort.98") as f:
        #    lines = f.readlines()
        lines = self.readFort98()
        if ("ZZ(K)" in lines[self.headLineIdxOfZZ]):
            linePointer = self.headLineIdxOfZZ + 2
            while True:
                zz.append(float(lines[linePointer].split()[1]))
                linePointer += 1
                if ("=" in lines[linePointer]): break
        return np.array(zz)

    def loadZC(self):
        zz = []
        lines = self.readFort98()
        if ("ZT(K)" in lines[self.headLineIdxOfZZ]):
            linePointer = self.headLineIdxOfZZ + 2
            while True:
                zz.append(float(lines[linePointer].split()[2]))
                linePointer += 1
                if ("=" in lines[linePointer]): break
        return np.array(zz)

    def loadRHO(self):
        rho = []
        lines = self.readFort98()
        if ("RHO(K)" in lines[self.headLineIdxOfRho]):
            linePointer = self.headLineIdxOfRho + 2
            while True:
                rho.append(float(lines[linePointer].split()[1]))
                linePointer += 1
                if ("=" in lines[linePointer]): break
        return np.array(rho)

    def loadRHOZ(self):
        rho = []
        lines = self.readFort98()
        if ("RHOZ(K)" in lines[self.headLineIdxOfRhoz]):
            linePointer = self.headLineIdxOfRhoz + 2
            while True:
                rho.append(float(lines[linePointer].split()[1]))
                linePointer += 1
                if (lines[-1] in lines[linePointer]): 
                    rho.append(float(lines[linePointer].split()[1]))
                    break
        return np.array(rho)

    def loadPBAR(self):
        pbar = []
        lines = self.readFort98()
        if ("PBAR(K)" in lines[self.headLineIdxOfRho]):
            linePointer = self.headLineIdxOfRho + 2
            while True:
                pbar.append(float(lines[linePointer].split()[3]))
                linePointer += 1
                if ("=" in lines[linePointer]): break
        return np.array(pbar)

    def loadPIBAR(self):
        pbar = []
        lines = self.readFort98()
        if ("PIBAR(K)" in lines[self.headLineIdxOfRho]):
            linePointer = self.headLineIdxOfRho + 2
            while True:
                pbar.append(float(lines[linePointer].split()[4]))
                linePointer += 1
                if ("=" in lines[linePointer]): break
        return np.array(pbar)

    def readFort98(self):
        with open(self.dataDir + "fort.98") as f:
            lines = f.readlines()
        return lines
    def findheadLineIdx(self, checkStr):
        fort98 = self.readFort98()
        for i in range(len(fort98)):
            if checkStr in fort98[i]:
                return i

class VVMGeoLoader:
    def __init__(self, dataDir):
        self.dataDir = dataDir
        self.topoNC = Dataset(self.dataDir + "TOPO.nc")

    def loadVar(self, varName):
        return np.array(self.topoNC[varName])
