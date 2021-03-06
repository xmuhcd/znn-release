#!/usr/bin/env python
__doc__ = """

Jingpeng Wu <jingpeng.wu@gmail.com>, 2015
"""
import numpy as np
from matplotlib.pylab import plt
from os import path

class CLearnCurve:
    def __init__(self, fname=None):
        if fname is None:
            # initialize with empty list
            self.tt_it  = list()
            self.tt_err = list()
            self.tt_cls = list()

            self.tn_it  = list()
            self.tn_err = list()
            self.tn_cls = list()
        else:
            self._read_curve( fname )
        return

    def _read_curve(self, fname):
        # initialize by loading from a h5 file
        # get the iteration number
        iter_num = self._get_iter_num(fname)

        if 'statistics' not in fname:
            # it is the network file name
            fname = find_statistics_file_within_dir(fname)
        assert( path.exists(fname) )
        # read data
        import h5py
        # read into memory
        f = h5py.File(fname, 'r', driver='core')
        self.tt_it  = list( f['/test/it'].value )
        self.tt_err = list( f['/test/err'].value )
        self.tt_cls = list( f['/test/cls'].value )

        self.tn_it  = list( f['/train/it'].value )
        self.tn_err = list( f['/train/err'].value )
        self.tn_cls = list( f['/train/cls'].value )
        f.close()

        # crop the values
        if iter_num is not None:
            self._crop_iters(iter_num)
        return

    def _crop_iters(self, iter_num):

        # test iterations
        gen = (i for i,v in enumerate(self.tt_it) if v>iter_num)
        try:
            ind = next(gen)
            self.tt_it  = self.tt_it[:ind]
            self.tt_err = self.tt_err[:ind]
            self.tt_cls = self.tt_cls[:ind]
        except StopIteration:
            pass

        # train iterations
        gen = (i for i,v in enumerate(self.tn_it) if v>iter_num)
        try:
            ind = next(gen)
            self.tn_it  = self.tn_it[:ind]
            self.tn_err = self.tn_err[:ind]
            self.tn_cls = self.tn_cls[:ind]
        except StopIteration:
            pass

        return

    def _get_iter_num(self, fname ):
        if '.h5' not in fname:
            return None
        root, ext = path.splitext(fname)
        str_num = root.split('_')[-1]
        if 'current' in str_num or 'statistics' in str_num:
            # the last network
            return None
        else:
            return int(str_num)

    def append_test(self, it, err, cls):
        # add a test result
        self.tt_it.append(it)
        self.tt_err.append(err)
        self.tt_cls.append(cls)

    def append_train(self, it, err, cls):
        # add a training result
        self.tn_it.append(it)
        self.tn_err.append(err)
        self.tn_cls.append(cls)

    def get_last_it(self):
        # return the last iteration number
        if len(self.tt_it)>0 and len(self.tn_it)>0:
            last_it = max( self.tt_it[-1], self.tn_it[-1] )
            print "inherit last iteration: ", last_it
            return last_it
        else:
            return 0

    #%% smooth function
    def _smooth(self, x, y, w):
        # averaging the curve
        x = np.asarray(x)
        y = np.asarray(y)
        w = int(w)
        assert(w>0)
        assert(x.ndim==1)
        assert(y.ndim==1)
        lw = (w-1)/2
        rw = w/2

        x2 = list()
        y2 = list()
        for i in xrange(lw, x.size-rw, w):
            x2.append( x[i] )
            y2.append( np.mean( y[i-lw:i+rw+1] ) )
        return x2, y2

    def show(self, w):
        """
        illustrate the learning curve

        Parameters
        ----------
        w : int, window size for smoothing the curve
        """

        # plot data
        plt.subplot(121)
        plt.plot(self.tn_it, self.tn_err, 'b.', alpha=0.2)
        plt.plot(self.tt_it, self.tt_err, 'r.', alpha=0.2)
        # plot smoothed line
        xne,yne = self._smooth( self.tn_it, self.tn_err, w )
        xte,yte = self._smooth( self.tt_it, self.tt_err, w )
        plt.plot(xne, yne, 'b')
        plt.plot(xte, yte, 'r')
        plt.xlabel('iteration'), plt.ylabel('cost energy')

        plt.subplot(122)
        plt.plot(self.tn_it, self.tn_cls, 'b.', alpha=0.2)
        plt.plot(self.tt_it, self.tt_cls, 'r.', alpha=0.2)
        # plot smoothed line
        xnc, ync = self._smooth( self.tn_it, self.tn_cls, w )
        xtc, ytc = self._smooth( self.tt_it, self.tt_cls, w )
        plt.plot(xnc, ync, 'b', label='train')
        plt.plot(xtc, ytc, 'r', label='test')
        plt.xlabel('iteration'), plt.ylabel( 'classification error' )
        plt.legend()
        plt.show()
        return

    def save( self, pars, elapsed):
        # get filename
        fname = pars['train_save_net']
        import os
        root, ext = os.path.splitext(fname)
        fname = root + '_statistics_current.h5'
        if os.path.exists( fname ):
            os.remove( fname )

        # save variables
        import h5py
        f = h5py.File( fname )
        f.create_dataset('train/it',  data=self.tn_it)
        f.create_dataset('train/err', data=self.tn_err)
        f.create_dataset('train/cls', data=self.tn_cls)
        f.create_dataset('test/it',   data=self.tt_it)
        f.create_dataset('test/err',  data=self.tt_err)
        f.create_dataset('test/cls',  data=self.tt_cls)
        f.create_dataset('elapsed',   data=elapsed)
        f.close()

        # move to new name
        fname2 = root + '_statistics.h5'
        os.rename(fname, fname2)

def find_statistics_file_within_dir(seed_filename):
    '''
    Looks for the stats file amongst the directory where
     the loaded network is stored
    '''
    import glob

    containing_directory, filename = path.split(seed_filename)

    #First attempt- if there's only one stats file, take it
    candidate_files = glob.glob( "{}/*statistics*".format(containing_directory) )

    some_stats_files_in_load_directory = len(candidate_files) > 0
    assert(some_stats_files_in_load_directory)

    #Next attempt- split filename by '_' and search for more specific files
    # until only one remains

    filename_fields = filename.split('_')
    filename_fields.reverse()

    first_field = filename_fields.pop()
    search_expression_head = containing_directory + "/" + first_field
    while len(candidate_files) > 1:
        candidate_files = glob.glob( search_expression_head + "*statistics*" )

        stats_search_found_a_file = len(candidate_files) > 0
        assert(stats_search_found_a_file)

        search_expression_head += '_' + filename_fields.pop()

    return candidate_files[0]

if __name__ == '__main__':
    """
    show learning curve

    usage
    ----
    python statistics.py path/of/statistics.h5 5
    5 is an example of smoothing window size
    """
    import sys
    # default window size
    w = 3

    if len(sys.argv)==2:
        fname = sys.argv[1]
        lc = CLearnCurve( fname )
    elif len(sys.argv)==3:
        fname = sys.argv[1]
        lc = CLearnCurve( fname )
        w = int( sys.argv[2] )
        print "window size: ", w
    else:
        raise NameError("no input statistics h5 file!")

    lc.show( w )
