import numpy as np
import netCDF4 as nc
import sys
import xarray as xr
sys.path.insert(0, "../")
import config
from util.vvmLoader import VVMLoader
from util.dataWriter import DataWriter
import matplotlib.pyplot as plt

def getStreamFunc(eta, relativeError, rho3D, dx, dzz3D, dzc3D):
    streamFunc = np.zeros(shape=eta.shape)
    prevSF = np.zeros(shape=eta.shape)
    error = 10
    iterLim, iterNum = 300, 0
    denominator = rho3D[1:-1] * (2 / (dx ** 2) + 1 / (dzz3D[:-2] * dzc3D[1:]) + 1 / (dzz3D[:-2] + dzc3D[:-1]))
    while error >= relativeError and iterNum <= iterLim:
        phiKp1 = np.roll(prevSF[1:-1], -1, axis=0)
        phiKm1 = np.roll(prevSF[1:-1],  1, axis=0)
        phiIp1 = np.roll(prevSF[1:-1], -1, axis=1)
        phiIm1 = np.roll(prevSF[1:-1],  1, axis=1) 
        streamFunc[1:-1] = (rho3D[1:-1] * eta[1:-1] + \
                            rho3D[1:-1] * (phiIp1 + phiIm1) / (dx ** 2) + \
                            ((rho3D[2:] * phiKp1 / dzc3D[1:]) + (rho3D[:-2] * phiKm1 / dzc3D[:-1])) / (dzz3D[:-2])
                           ) / denominator

        streamFunc[0] = 0
        streamFunc[-1] = 0
        error = np.mean((streamFunc - prevSF) ** 2) ** (1/2)
        prevSF = streamFunc.copy()
        iterNum += 1
        #if iterNum % 100 == 0:
        print(iterNum, error)
    return streamFunc


if __name__ == "__main__":
    iniTimeIdx, endTimeIdx, caseIdx = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    caseName = config.caseNames[caseIdx]
    vvmLoader = VVMLoader(dataDir=f"{config.vvmPath}{caseName}/", subName=caseName)
    rho3D = vvmLoader.loadRHO()[:-1][:, np.newaxis]
    zz3D = vvmLoader.loadZZ()[:, np.newaxis]
    dzz3D = zz3D[1:] - zz3D[:-1]
    thData = vvmLoader.loadThermoDynamic(0)
    xc, yc, zc = np.array(thData["xc"]), np.array(thData["yc"]), np.array(thData["zc"])
    dx = xc[1] - xc[0]
    dzc3D = (zc[1:] - zc[:-1])[:, np.newaxis]
    dataWriter = DataWriter(outputPath = f"{config.streamFuncAvePath}{caseName}/")
    timeArange = np.arange(iniTimeIdx, endTimeIdx, 1)
    relativeError = 1e-6
    for tIdx in timeArange:
        print(f"========== {tIdx:06d} ==========")
        dyData = vvmLoader.loadDynamic(tIdx)
        eta  = - np.array(dyData["eta"][0])
        #zeta = np.array(dyData["zeta"][0])
        
        eta = (np.roll(eta, (1, 1), axis=(0, 2)) + eta) / 2
        eta = np.mean(eta, axis=1)
        #zeta= (np.roll(zeta, (1, 1), axis=(1, 2)) + zeta) / 2
    
        sf = getStreamFunc(eta, relativeError, rho3D, dx, dzz3D, dzc3D)

        dataWriter.toNC(f"streamFunc-{tIdx:06d}.nc", sf[np.newaxis, :, :],
                        coords = {'time': np.ones(shape=(1,)), 'zc': zc, 'xc': xc},
                        dims = ["time", "zc", "xc"],
                        varName = "streamFunc")
