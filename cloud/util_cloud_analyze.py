import numpy as np
from scipy import ndimage
from functools import cache
import multiprocessing
import os, sys

class CloudRetriever:
    def __init__(self, data, threshold=1e-5, domain=None, cc_condi=None, cores=5, debug_level=0):
        self._debug       = debug_level
        self.cld_data     = data
        self.cld_th       = threshold
        self.domain       = domain or self._default_domain(self.cld_data)
        self.cores        = cores

        if self._debug >= 1 : print('===== Labeling cloud and find their feature -----')
        self.cld_label, self.cld_n    = \
            self.label_regions_with_dynamic_periodic_boundary(\
                mask = self.cld_data >= self.cld_th, \
                struct = self._get_connect_structure(),\
            )
        self.cld_index = np.arange(1, self.cld_n+1)
        self.cld_feat  = self._get_feature(self.cld_data, self.cld_label, self.cld_index)
        if type(None) != type(cc_condi):
          self.cld_feat['cc_flag']  = self._examine_convective_cloud(self.cld_feat, cc_condi)

    def _get_feature(self, data, label, index):
        feature = {}
        if self._debug >= 1 : print('[feature] centroid, size, top, base ...')
        feature['center_zyx'], feature['size'], feature['top'], feature['base'] = \
            self._get_objects_feature_multicore(data, label, index, cores=self.cores)

        return feature

    def cal_convective_core_clouds(self, data_w):
        if self._debug >= 1 : print('===== Labeling ccc and find their features  ...')
        self._ccc_mask = self._get_convective_core_cloud_mask(data_w)

        self.ccc_label, self.ccc_n = \
            self.label_regions_with_dynamic_periodic_boundary(\
                mask = self._ccc_mask, \
                struct = self._get_connect_structure(),\
            )
        self.ccc_index = np.arange(1, self.ccc_n+1)

        self.ccc_feat  = self._get_feature(self.cld_data, self.ccc_label, self.ccc_index)
        return

    def _get_an_object_feature(self, label, weights, dx, dy, dz, lbl):
        if self._debug >= 2: print(f'[feat, center]: calculate mass of center ... {lbl}')

        # Convert to angles
        L_x = self.domain['x'].max()
        L_y = self.domain['y'].max()
        theta_x = (2 * np.pi * self.domain['x'] / L_x )
        theta_y = (2 * np.pi * self.domain['y'] / L_y )
        lev_z   = np.copy(self.domain['z'])

        idx = np.nonzero(label==lbl)
        # object size
        num  = np.size(idx[0])
        objsize = np.sum(dx[idx[2]] * dy[idx[1]] * dz[idx[0]])

        # cloud_top_and_base
        hei = self.domain['z'][idx[0]]
        top, base = np.max(hei), np.min(hei)

        # cloud centroid
        lbl_weights = weights[idx] # 1-d array
        lbl_z =   lev_z[idx[0]]
        lbl_y = theta_y[idx[1]]
        lbl_x = theta_x[idx[2]]

        sum_lbl_weights = np.sum(lbl_weights)
        centeroid_z = np.sum(lbl_weights * lbl_z) / sum_lbl_weights

        s_x = np.sum(lbl_weights * np.sin(lbl_x)) / sum_lbl_weights
        c_x = np.sum(lbl_weights * np.cos(lbl_x)) / sum_lbl_weights
        s_y = np.sum(lbl_weights * np.sin(lbl_y)) / sum_lbl_weights
        c_y = np.sum(lbl_weights * np.cos(lbl_y)) / sum_lbl_weights 
        shift_theta_x = np.arctan2(s_x, c_x)
        shift_theta_y = np.arctan2(s_y, c_y)
        centroid_x = ( (shift_theta_x * L_x) / (2 * np.pi) ) % L_x
        centroid_y = ( (shift_theta_y * L_y) / (2 * np.pi) ) % L_y


        return centeroid_z, centroid_y, centroid_x, num, objsize, top, base
        


    def _get_objects_feature_multicore(self, weights_positive, label, index, cores):
        #calculate_weighted_centroid_periodic_zyx(self, weights_positive, label, index)

        # Use multiprocessing to fetch variable data in parallel
        dx = np.gradient(self.domain['x'])
        dy = np.gradient(self.domain['y'])
        dz = np.diff(self.domain['zz'])

        # Use multiprocessing to fetch variable data in parallel
        with multiprocessing.Pool(processes=cores) as pool:
            obj_feat = pool.starmap(self._get_an_object_feature, \
                                    [(label, weights_positive, dx, dy, dz, lbl) for lbl in index] )
        obj_feat = np.array(obj_feat)
        obj_centorid = obj_feat[:,:3]
        obj_size = obj_feat[:,3:5]
        obj_top  = obj_feat[:, 5]
        obj_base = obj_feat[:, 6]

        return obj_centorid, obj_size, obj_top, obj_base


    def _examine_convective_cloud(self, feat, condiction):
        if self._debug >= 1: print('[feature] examine_convective_cloud')
        condi = np.ones(feat['base'].shape, dtype=bool)
        if 'base' in condiction.keys():
          condi *= (feat['base'] <= condiction['base'])
        if 'top' in condiction.keys():
          condi *= (feat['top'] >= condiction['top'])
        cc_flag = np.where(condi, 1, 0)
        return cc_flag

    def _get_convective_core_cloud_mask(self, w):
        # intersection between vertical velocity(w) > 0.5 m/s
        # and convective cloud [qc+qi>0.5, base<2km]
     
        cc_index = self.cld_index[self.cld_feat['cc_flag'].astype(bool)]
        cc_mask  = np.isin(self.cld_label, cc_index)
        w_mask   = np.where(w>=0.5, True, False)
        ccc_mask = cc_mask * w_mask
        return ccc_mask
       
    def _default_domain(self, data):
        domain = {}
        shape  = data.shape
        domain['z'] = np.arange(shape[0])+0.5
        domain['zz'] = np.arange(shape[0]+1)
        domain['y'] = np.arange(shape[1])
        domain['x'] = np.arange(shape[2])
        return domain

    def _get_cloud_base_and_top(self, label, index):
        shape  = label.shape
        zc3d = np.ones(shape) * self.domain['z'][:, np.newaxis, np.newaxis]
        extrema = ndimage.extrema(zc3d, label, index=index)
        base = extrema[0]
        top  = extrema[1]
        return base, top

    def _get_connect_structure(self):
        structure = np.array([[[0, 0, 0],
                               [0, 1, 0],
                               [0, 0, 0]],
                              [[0, 1, 0],
                               [1, 1, 1],
                               [0, 1, 0]],
                              [[0, 0, 0],
                               [0, 1, 0],
                               [0, 0, 0]]])
        return structure
    


    def label_regions_with_dynamic_periodic_boundary(self, mask, struct):
        """
        Label regions greater than the threshold with consideration for periodic boundaries in x and y directions.
        
        Args:
            data (numpy.ndarray): A 3D array with shape (nz, ny, nx).
            threshold (float): Threshold value; regions greater than this will be labeled.
    
        Returns:
            numpy.ndarray: A labeled array of the same shape as the input, with continuous increasing labels.
        """
        if self._debug >= 1: print('[Label] start to label data ... ')
        nz, ny, nx = mask.shape
        
        # Initial labeling of connected regions
        labeled, num_features = ndimage.label(mask, structure=struct)
    
        parent = np.arange(num_features+1)  # assume label_array is contious
   
        def find_root(lbl):
            record=np.array([lbl])
            while lbl != parent[lbl]:
                #parent[lbl] = parent[parent[lbl]]
                lbl = parent[lbl]
                record = np.append(lbl, record)
            parent[record] = lbl
            return lbl
    
        def union_labels(label1, label2):
            """Union two sets of labels."""
            root1 = find_root(label1)
            root2 = find_root(label2)
            if root1 != root2:
                parent[root2] = root1
   
        # check and merge periodic boundary labels
        # --> modify the parent array
        active_x = np.nonzero(mask[:, :, 0] * mask[:, :, -1])
        active_y = np.nonzero(mask[:, 0, :] * mask[:, -1, :])
        for z, y in zip(*active_x):
            union_labels(labeled[z, y, 0], labeled[z, y, -1])
        for z, x in zip(*active_y):
            union_labels(labeled[z, 0, x], labeled[z, -1, x])

        # redistribute and ensure boundary label is link to root object
        check_label = np.array([0])
        if len(active_x[0]) > 0:
            check_label = np.concatenate((check_label,\
                                         labeled[active_x[0], active_x[1], 0],\
                                         labeled[active_x[0], active_x[1], -1]))
        if len(active_y[0]) > 0:
            check_label = np.concatenate((check_label,\
                                         labeled[active_y[0], 0,  active_y[1]],\
                                         labeled[active_y[0], -1, active_y[1]]))
        for lbl in np.unique(check_label):
            dum = find_root(lbl)

        # create unique inverse parent_array
        if self._debug >= 2: print(f'[Label] origin parent ... {parent}')
        uni, new_parent = np.unique(parent, return_inverse=True)
        if self._debug >= 2: print(f'[Label]    new parent ... {new_parent}')
       
        labeled = new_parent[labeled]
        num = np.size(uni)-1
    
        return labeled, num


if __name__=='__main__':
    from netCDF4 import Dataset
    it = 1800
    exp = 'RRCE_3km_f00'
    # it = 216
    # exp = 'RRCE_3km_f00_20'
    fname = f'/data/C.shaoyu/rrce/vvm/{exp}/archive/{exp}.L.Thermodynamic-{it:06d}.nc'
    thNC = Dataset(fname, 'r')
    fname = f'/data/C.shaoyu/rrce/vvm/{exp}/archive/{exp}.L.Dynamic-{it:06d}.nc'
    dyNC = Dataset(fname, 'r')
    domain = {'x': thNC['xc'][:]/1000.,\
              'y': thNC['yc'][:]/1000.,\
              'z': thNC['zc'][:]/1000.,\
             }
    data_cld = thNC['qc'][0] + thNC['qi'][0]
    data_cld[0] = 0.
    data_w   = np.zeros(data_cld.shape)
    data_w[1:]  = (dyNC['w'][0,:-1] + dyNC['w'][0,1:]) / 2
    thNC.close()
    dyNC.close()

    fname = f'../../vvm/{exp}/fort.98'
    zz = np.loadtxt(fname, skiprows=188, max_rows=domain['z'].size, usecols=1)
    zz = np.concatenate(([0], zz)) # zc bound
    domain['zz'] = zz/1000.

    cloud = CloudRetriever(data_cld, threshold=1e-5, domain=domain, cc_condi={'base':2}, debug_level=1, cores=5)
    cloud.cal_convective_core_clouds(data_w)


    import matplotlib.pyplot as plt
    fname = f'../../data/wp/{exp}/wp-{it:06d}.nc'
    nc = Dataset(fname, 'r')
    cwv = nc.variables['cwv'][0,:]
    nc.close()
    # zyx = cloud.ccc_feat['center_zyx']
    # plt.figure(); plt.hist(zyx[:,2],bins=np.arange(0, 1200, 50)); plt.title('xc')
    # plt.figure(); plt.hist(zyx[:,1],bins=np.arange(0, 1200, 50)); plt.title('yc')
    # plt.figure(); plt.hist(zyx[:,0],bins=np.arange(0, 16,0.5)); plt.title('zc')

    plt.figure()
    plt.contourf(domain['x'], domain['y'], cwv, levels=np.arange(10,61,5), cmap=plt.cm.Greens)
    zyx = cloud.cld_feat['center_zyx']
    size = (cloud.cld_feat['size'][:,1])**(1/3)
    for i in range(cloud.cld_n):
        co = 'b' if cloud.cld_feat['cc_flag'][i] else 'k'
        si = size[i]
        plt.scatter(zyx[i,2], zyx[i,1], s=si, c=co)

    zyx_ccc = cloud.ccc_feat['center_zyx']
    size_ccc = cloud.ccc_feat['size'][:,1]**(1/3)
    for i in range(cloud.ccc_n):
      co  = 'r'
      si  = size_ccc[i]
      plt.scatter(zyx_ccc[i,2], zyx_ccc[i,1], s=si, c=co)
    plt.xlim(domain['x'].min(), domain['x'].max())
    plt.ylim(domain['y'].min(), domain['y'].max())
    plt.xlabel('[m]')
    plt.ylabel('[m]')
    plt.title('location of ccc[red] / cc[blue] / cld[black]')
    plt.show()

    sys.exit()
    shape = (5, 10, 10)
    data = np.zeros(shape)
    data[4, :2, 2:5] = 3
    data[:4, :2, :2] = 10
    data[:4, :2, -2:] = 13
    data[:4, -1:, :2] = 15
    data[3, 3:5, :5] = 22
    #data[3,  :, -1] = 20

    data[2:5, 3:6, 5:7] = 18
    data[0, 2:6, 5:8]  = 19

    cloud = CloudRetriever(data, threshold=0.5, debug_level=2, cores=5)
    
    print("Original array:")
    print(cloud.cld_data)
    print("Labeled array:")
    print(cloud.cld_label)
