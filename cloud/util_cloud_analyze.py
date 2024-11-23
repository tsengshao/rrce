import numpy as np
from scipy import ndimage
from functools import cache
import multiprocessing

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
        if self._debug >= 1 : print('[feature] calculate center of object mass ...')
        feature['center_zyx'] = self._get_object_center_of_mass(data, label, index, cores=self.cores)

        if self._debug >= 1 : print('[feature] calculate object base/top and convective cloud ...')
        feature['base'], feature['top'] = \
            self._get_cloud_base_and_top(label, index)
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

    def _get_an_object_centorid(self, label, weights, lbl):
        if self._debug >= 2: print(f'[feat, center]: calculate mass of center ... {lbl}')

        # Convert to angles
        L_x = self.domain['x'].max()
        L_y = self.domain['y'].max()
        theta_x = (2 * np.pi * self.domain['x'] / L_x )
        theta_y = (2 * np.pi * self.domain['y'] / L_y )
        lev_z   = np.copy(self.domain['z'])

        idx = np.nonzero(label==lbl)
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
        return centeroid_z, centroid_y, centroid_x
        


    def _get_object_center_of_mass(self, weights_positive, label, index, cores=5):
        #calculate_weighted_centroid_periodic_zyx(self, weights_positive, label, index)
    
        ##------------------------------------------------
        ## find the positive value centeroid
        ## ------
        # obj_centorid = []
        # for lbl in index:
        #     centorid = self.__get_an_object_centorid(label, weights_positive, lbl)
        #     obj_centorid.append( centorid )

        # Use multiprocessing to fetch variable data in parallel
        with multiprocessing.Pool(processes=cores) as pool:
            obj_centorid = pool.starmap(self._get_an_object_centorid, [(label, weights_positive, lbl) for lbl in index] )
        obj_centorid = np.array(obj_centorid)

        return obj_centorid


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
        domain['z'] = np.arange(shape[0])
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
    
        # Handle periodic boundary conditions and merge labels
        def merge_labels(label_array, nz, ny, nx):
            """Handle periodic boundary conditions and merge labels using union-find with path compression."""
            parent = {}
   
            @cache
            def find_root(label):
                """Find the root of a label using path compression."""
                if parent[label] != label:
                    parent[label] = find_root(parent[label])  # Path compression
                return parent[label]
    
            def union_labels(label1, label2):
                """Union two sets of labels."""
                root1 = find_root(label1)
                root2 = find_root(label2)
                if root1 != root2:
                    parent[root2] = root1
   
            # Initialize the union-find structure
            unique_labels = np.unique(label_array)
            for lbl in unique_labels:
                if lbl > 0:  # Ignore background labels
                    parent[lbl] = lbl

            # Check and merge periodic boundary labels
            for z in range(nz):
                if self._debug >= 2: print(f'check z {z} ...')
                for y in range(ny):
                    if label_array[z, y, 0] > 0 and label_array[z, y, nx - 1] > 0:
                        union_labels(label_array[z, y, 0], label_array[z, y, nx - 1])
                for x in range(nx):
                    if label_array[z, 0, x] > 0 and label_array[z, ny - 1, x] > 0:
                        union_labels(label_array[z, 0, x], label_array[z, ny - 1, x])
    
            # Replace labels with their root labels
            for lbl in unique_labels:
                if self._debug >= 2: print(f'replace_label lbl {lbl} ... ')
                if lbl > 0:
                    root = find_root(lbl)
                    label_array[label_array == lbl] = root
    
            # Ensure labels are continuous and increasing
            unique_labels = np.unique(label_array)
            label_array_new = np.zeros(label_array.shape, dtype=int)
            for ilbl in range(len(unique_labels)):
                label_array_new[label_array == unique_labels[ilbl]] = ilbl
    
            return label_array_new
    
        # Merge periodic boundary labels and relabel to ensure continuity
        labeled = merge_labels(labeled, nz, ny, nx)
        num = np.unique(labeled).size-1
    
        return labeled, num


if __name__=='__main__':
    from netCDF4 import Dataset
    it = 1440
    exp = 'RRCE_3km_f00'
    # it = 216
    # exp = 'RRCE_3km_f00_20'
    fname = f'/data/C.shaoyu/rrce/vvm/{exp}/archive/{exp}.L.Thermodynamic-{it:06d}.nc'
    thNC = Dataset(fname, 'r')
    fname = f'/data/C.shaoyu/rrce/vvm/{exp}/archive/{exp}.L.Dynamic-{it:06d}.nc'
    dyNC = Dataset(fname, 'r')
    domain = {'x': thNC['xc'][:],\
              'y': thNC['yc'][:],\
              'z': thNC['zc'][:],\
             }
    data_cld = thNC['qc'][0] + thNC['qi'][0]
    data_w   = np.zeros(data_cld.shape)
    data_w[1:]  = (dyNC['w'][0,:-1] + dyNC['w'][0,1:]) / 2
    thNC.close()
    dyNC.close()

    cloud = CloudRetriever(data_cld, threshold=1e-5, domain=domain, cc_condi={'base':2000}, debug_level=1, cores=10)
    cloud.cal_convective_core_clouds(data_w)

    import matplotlib.pyplot as plt
    zyx = cloud.ccc_feat['center_zyx']/1000
    plt.figure(); plt.hist(zyx[:,2],bins=np.arange(0, 1200, 50)); plt.title('xc')
    plt.figure(); plt.hist(zyx[:,1],bins=np.arange(0, 1200, 50)); plt.title('yc')
    plt.figure(); plt.hist(zyx[:,0],bins=np.arange(0, 16,0.5)); plt.title('zc')

    plt.figure()
    zyx = cloud.cld_feat['center_zyx']
    cc  = np.nonzero(cloud.cld_feat['cc_flag']>0.5)[0]
    plt.scatter(zyx[:,2], zyx[:,1], c='k')
    plt.scatter(zyx[cc,2], zyx[cc,1], c='b')

    zyx_ccc = cloud.ccc_feat['center_zyx']
    plt.scatter(zyx_ccc[:,2], zyx_ccc[:,1], c='r')
    plt.xlim(domain['x'].min(), domain['x'].max())
    plt.ylim(domain['y'].min(), domain['y'].max())
    plt.xlabel('[m]')
    plt.ylabel('[m]')
    plt.title('location of ccc[red] / cc[blue] / cld[black]')
    plt.show()





    ## shape = (5, 10, 10)
    ## data = np.zeros(shape)
    ## data[4, :2, 2:5] = 3
    ## data[:4, :2, :2] = 10
    ## data[:4, :2, -2:] = 13
    ## data[:4, -1:, :2] = 15
    ## data[3, 3:5, :5] = 22
    ## #data[3,  :, -1] = 20

    ## data[2:5, 3:6, 5:7] = 18
    ## data[0, 2:6, 5:8]  = 19
    
    ## labeled_regions = label_regions_with_dynamic_periodic_boundary(data, threshold)
    ## cloud = util_cloud(data_cld, threshold=1e-5)
    
    ## print("Original array:")
    ## print(cloud.cld_data)
    ## print("Labeled array:")
    ## print(cloud.cld_label)
