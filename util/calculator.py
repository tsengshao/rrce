import sys
import numpy as np
from scipy.signal import correlate2d, correlate, gaussian
from scipy.ndimage import laplace
from multiprocessing import Pool

# ========== Constant
Lv = 2.5e6
Cp = 1004
g = 9.81
Rd = 287

def getiLoniLat(lon, lat, lonb, latb):
    ilon0 = np.argmin(np.abs(lon-lonb[0]))
    ilon1 = np.argmin(np.abs(lon-lonb[1]))
    ilat0 = np.argmin(np.abs(lat-latb[0]))
    ilat1 = np.argmin(np.abs(lat-latb[1]))
    ilon = slice(ilon0, ilon1+1, 1)
    if ilat0>ilat1:
      ilat = slice(ilat0, ilat1-1, -1)
    else:
      ilat = slice(ilat0, ilat1+1, 1)
    return ilon, ilat

def getPseudoAlbedo(nc, qc, deltaZZ, rho3D):
    colNC = np.sum((nc * deltaZZ)[1:], axis=0)
    LWP = np.sum((rho3D * qc * deltaZZ)[1:], axis=0)
    cloudOptDept = 0.19 * (LWP ** (5 / 6)) * (colNC ** (1 / 3))
    A = cloudOptDept / (6.8 + cloudOptDept)
    return A

def hrzAveCoarsen(data, numFrameY, numFrameX):
    presentPoints = []
    averageData = np.zeros(shape=(data.shape[0], data.shape[1]+1, data.shape[2]+1))
    averageData[:, 0:-1, 0:-1] = data
    for yIdx in np.arange(0, data.shape[1]+1, numFrameY):
        for xIdx in np.arange(0, data.shape[2]+1, numFrameX):
            presentPoints.append([yIdx, xIdx])
    for p in presentPoints:
        averageData[:, p[0]:p[0]+numFrameY, p[1]:p[1]+numFrameX] = np.mean(averageData[:, p[0]:p[0]+numFrameY, p[1]:p[1]+numFrameX], axis=(1, 2), keepdims=True)
    return averageData[:, :-1, :-1]

def vtcAveCoarsen(data, numFrameZ, deltaZZ3D, totalDeltaZZ3D):
    averageData = np.zeros(shape=(data.shape[0]+1, data.shape[1], data.shape[2]))
    averageData[0:-1, 0:, 0:] = data

    for i in range(len(zc)+1)[::5]:
        averageData[i:i+numFrameZ, :, :] = np.sum(averageData[i:i+numFrameZ, :, :] * deltaZZ3D[i:i+numFrameZ, :, :], axis=0, keepdims=True)
    averageData = averageData[:-1, :, :]
    averageData = averageData / totalDeltaZZ3D
    #averageData[len(zc)-numFrameZ:] = np.sum(averageData[len(zc)-numFrameZ:, :, :] * deltaZZ3D[len(zc)-numFrameZ:, :, :], axis=(0), keepdims=True)
    return averageData

def getConvolveWeight(hrzFrameSize):
    """
    INPUT: hrzFrameSize, only positive integer or XX.5 is accepted currently
    """
    integerPart, decimalPart = int(hrzFrameSize), round(hrzFrameSize - int(hrzFrameSize), 1)
    closestOddNum = integerPart if integerPart % 2 == 1 else integerPart - 1
    weightBoundVal = np.round(((integerPart - closestOddNum) + decimalPart) / 2, 2)
    weightSize = closestOddNum + 2 * (weightBoundVal != 0.0)
    weight2D = np.full(fill_value = 1., shape=(weightSize, weightSize))
    
    if (weightBoundVal != 0.0):    
        weight2D[0, :]  *= weightBoundVal
        weight2D[-1, :] *= weightBoundVal
        weight2D[:, 0]  *= weightBoundVal
        weight2D[:, -1] *= weightBoundVal
     
    return weight2D

def getExpandSize(weight):
    if weight.shape[0] % 2 == 1:
        expandSize = (weight.shape[0] - 1) // 2
    else:
        expandSize = (weight.shape[0] - 1) // 2 + 1
    return expandSize

def getExpandData(data, weight):
    expandSize = getExpandSize(weight)
    expandData = np.pad(data, 
                        pad_width=((0, 0), 
                                   (expandSize, expandSize), 
                                   (expandSize, expandSize)), 
                        mode="wrap")
    return expandData

def getConvolve(data, hrzFrameSize, method="auto"):
    """method: direct / fft (error: O(1e-16))"""
    if method == "auto":
        method = chooseConvolMethod(hrzFrameSize)

    weight = getConvolveWeight(hrzFrameSize)
    expandSize = getExpandSize(weight)
    expandData = getExpandData(data, weight)
    convData = np.zeros(shape=data.shape)
    for i in range(data.shape[0]):
        print(i, data.shape[0])
        convData[i] = (correlate(expandData[i], weight, method=method) / (hrzFrameSize**2))[2*expandSize:-2*expandSize, 2*expandSize:-2*expandSize]
    return convData

def chooseConvolMethod(hrzFrameSize, maxThres=10):
    if hrzFrameSize >= maxThres:
        return "fft"
    else:
        return "direct"

def getHrzLaplacian(data):
    laplacianData = np.zeros(shape=data.shape)
    for i in range(data.shape[0]):
        laplace(data[i], output=laplacianData[i], mode='wrap')
    return laplacianData


# ========= multi-processing ========
def convolve(data, weight, hrzFrameSize, expandSize, i, method="direct"):
    if method == "direct":
        convolveData = ((correlate2d(data[i], weight)) / (hrzFrameSize**2))[2*expandSize:-2*expandSize, 2*expandSize:-2*expandSize]
    elif method == "fft":
        convolveData = ((correlate(data[i], weight, method="fft")) / (hrzFrameSize**2))[2*expandSize:-2*expandSize, 2*expandSize:-2*expandSize]
    return convolveData

def partitionDataPool(data, smallArrShape, expandSize):
    inputData = [data[:smallArrShape+expandSize*2, :smallArrShape+expandSize*2], 
                 data[-smallArrShape-expandSize*2:, :smallArrShape+expandSize*2], 
                 data[:smallArrShape+expandSize*2, -smallArrShape-expandSize*2:], 
                 data[-smallArrShape-expandSize*2:, -smallArrShape-expandSize*2:]]
    return inputData

def combinePartitionData(partitionData, smallArrShape, outputData):
    outputData[:smallArrShape, :smallArrShape] = partitionData[0]
    outputData[-smallArrShape:, :smallArrShape] = partitionData[1]
    outputData[:smallArrShape, -smallArrShape:] = partitionData[2]
    outputData[-smallArrShape:, -smallArrShape:] = partitionData[3]
    return outputData

# ========== Gaussian Kernel =========
def getGaussianWeight(kernelSize, std=1, normalize=True):
    gaussian1D = gaussian(kernelSize, std)
    gaussian2D = np.outer(gaussian1D, gaussian1D)
    if normalize:
        gaussian2D /= gaussian2D.sum()
    return gaussian2D

def getGaussianConvolve(data, kernel, method="fft"):
    """method: direct / fft (error: O(1e-16))"""
    ny, nx = data.shape[1], data.shape[2]
    expandLength = min(nx, ny)
    expandSize = getExpandSize(kernel)
    expandData = np.pad(data, 
                        pad_width=((0, 0), 
                                   (expandLength//2, expandLength//2), 
                                   (expandLength//2, expandLength//2)), 
                        mode="wrap")
    convData = np.zeros(shape=data.shape)

    for i in range(data.shape[0]):
        print(i, data.shape[0])
        convData[i] = correlate(expandData[i], kernel, method=method)[2*expandSize:-2*expandSize+1, 2*expandSize:-2*expandSize+1]
    return convData

# ========== get variables ==========
def getTemperature(theta, pBar=None, piBar=None):
    if pBar is not None:
        temp = theta * ((pBar / 100000) ** (Rd / Cp))
    elif piBar is not None:
        temp = theta * piBar
    return temp

def getMSE(temperature, zc3D, qv):
    mse = Cp * temperature + g * zc3D + Lv * qv
    return mse

# crate pseudo-adiabatic / dry-adiabatic
def cal_saturated_vapor_pressure(T_K):
    T_K = np.where(T_K-273.15<-50, -50+273.15, T_K)
    # Goff-Gratch formulation, ICE
    esi_hPa = 10.**(-9.09718*(273.16/T_K-1)\
                    -3.56654*np.log10(273.16/T_K)\
                    +0.876793*(1-T_K/273.16)\
                    +np.log10(6.1071))
    # Goff-Gratch formulation, LIQUID
    es_hPa = 10**(-7.90298*(373.16/T_K-1)\
                 +5.02808*np.log10(373.16/T_K)\
                 -1.3816e-7*(10**(11.344*(1-T_K/373.16))-1)\
                 +8.1328e-3*(10**(-3.49149*(373.16/T_K-1))-1)\
                 +np.log10(1013.246))
    #es_hPa = 6.112 * np.exp(17.67 * (T_K - 273.15)/ (T_K - 29.65))
    return np.where(T_K>=273.15, es_hPa, esi_hPa)

def cal_absolute_humidity(vapor_pressure_hPa,pressure_hPa):
    #dum = np.where((pressure_hPa-vapor_pressure_hPa)<1e-5, 1e-5, pressure_hPa-vapor_pressure_hPa)
    dum = pressure_hPa-vapor_pressure_hPa
    mixing_ratio = 0.622*vapor_pressure_hPa/dum
    specific_humidity = mixing_ratio/(1+mixing_ratio)
    return specific_humidity, mixing_ratio

def cal_equivalent_potential_temperature(P_hPa, rv_kgkg, t_K):
    #theta_e_K = t_K*(1000/P_hPa)**(287.05/1004)*np.exp(2.5e6*rv_kgkg/1004/t_K)
    theta_e_K = (t_K+2.5e6/1004*rv_kgkg)*(1000/P_hPa)**(287.05/1004)
    return theta_e_K
def cal_potential_temperature(P_hPa, T_K):
    theta_K = T_K*(1000/P_hPa)**(287.05/1004)
    return theta_K
def cal_saturated_rv(P_hPa,T_K):
    es_hPa = cal_saturated_vapor_pressure(T_K)
    qv, rv = cal_absolute_humidity(es_hPa, P_hPa)
    #print(es_hPa, qv, rv)
    return qv, rv

def parcel_profile_2d(Temp02d_K,Press1d_hPa, qv02d_kgkg, Height1d_m):
    # conservation of equivalent potential temperature and potential temperature
    # interpolate to conservate theta_e
    #trange=np.arange(-40,50,0.01)+273.15
    trange=np.arange(-60,50,0.05)+273.15
    tt,pp=np.meshgrid(trange,Press1d_hPa)
    es_hPa = cal_saturated_vapor_pressure(tt)
    qq, rr = cal_absolute_humidity(es_hPa, pp)
    #rr = np.where(pp<300, 0.0, rr)
    theta_e = cal_equivalent_potential_temperature(pp,rr,tt)-273.15
    theta_e = np.where(theta_e>500,np.nan,theta_e)

    nz, ny, nx = Press1d_hPa.size, Temp02d_K.shape[0], Temp02d_K.shape[1]
  
    temp_dry = (Temp02d_K.reshape(1,ny,nx))*(Press1d_hPa.reshape(nz,1,1)/Press1d_hPa[0])**0.2854
    qv, rv   = cal_saturated_rv(Press1d_hPa.reshape(nz,1,1), temp_dry)
    idxLCL = np.argmin(np.abs(qv-qv02d_kgkg.reshape(1,ny,nx)), axis=0)

    parcel3d = np.copy(temp_dry)
    idxLCL = idxLCL.reshape(ny,nx)
    idxY   = np.arange(ny).reshape(ny, 1)
    idxX   = np.arange(nx).reshape(1, nx)

    idxt2d = np.argmin(np.abs(trange.reshape(trange.size,1,1)-parcel3d[idxLCL, idxY, idxX].reshape(1,ny,nx)),axis=0)
    conserve_thetae2d = theta_e[idxLCL,idxt2d]

    idx200 = np.argmin(np.abs(Press1d_hPa-200))
    for idx in range(idx200):
      ind = np.where(idxLCL<=idx)
      if len(ind[0])==0: continue
      refresh = np.interp(conserve_thetae2d[ind], theta_e[idx,:], trange)
      parcel3d[idx*np.ones(ind[0].size,dtype=int),ind[0], ind[1]] = refresh
    for idx in range(idx200, nz):
      parcel3d[idx,:,:] = parcel3d[idx-1,:,:]-0.0098*(Height1d_m[idx]-Height1d_m[idx-1])
    return idxLCL, parcel3d

def cal_CAPE_CIN(temp_env_K, temp_parcel_K, Height_1d_m):
    (nz, ny, nx) = temp_env_K.shape
    dhei = np.diff(Height_1d_m).reshape(nz-1,1,1)
    diff = (temp_parcel_K-temp_env_K)/(temp_env_K)
    area = (diff[:-1]+diff[1:])*dhei/2*9.81

    idxEL = area.shape[0] - np.argmax(area[::-1,:,:]>=0, axis=0)
    idxEL3dmask = np.arange(nz-1).reshape(nz-1,1,1)<=idxEL.reshape(1,ny,nx)

    CAPE = np.sum(area, axis=0, where = (area>=0)*(idxEL3dmask))
    CIN  = np.sum(area, axis=0, where = (area<=0)*(idxEL3dmask))
    return CAPE, CIN


