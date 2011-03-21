
import os

import h5py, Image, numpy

from fnmatch import filter as fnfilter
from os.path import split as split_path, join as join_path
from numpy import array, asarray, uint8, uint16, uint32, zeros, squeeze

def read_image_stack(fn, *args, **kwargs):
    d, fn = split_path(fn)
    if len(d) == 0: d = '.'
    if kwargs.has_key('crop'):
        crop = kwargs['crop']
    else:
        crop = [None,None,None,None,None,None]
        kwargs['crop'] = crop
    if fn.endswith('.png'):
        if len(args) > 0 and type(args[0]) == str and args[0].endswith('png'):
            fns = [fn] + [split_path(f)[1] for f in args]
        else:
            fns = fnfilter(os.listdir(d), fn)
        fns.sort()
        fns = fns[crop[4]:crop[5]]
        ims = (Image.open(join_path(d,fn)) for fn in fns)
        ars = (asarray(im) for im in ims)
        w, h = asarray(Image.open(join_path(d,fns[0])))[crop[0]:crop[1],crop[2]:crop[3]].shape
        dtype = asarray(Image.open(join_path(d,fns[0]))).dtype
        stack = zeros([w,h,len(fns)], dtype)
        for i, im in enumerate(ars):
            stack[:,:,i] = im[crop[0]:crop[1],crop[2]:crop[3]]
    if fn.endswith('.h5'):
        stack = read_h5_stack('/'.join([d,fn]), *args, **kwargs)
    return squeeze(stack)

def read_h5_stack(fn, *args, **kwargs):
    if len(args) > 0:
        group = args[0]
    elif kwargs.has_key('group'):
        group = kwargs['group']
    else:
        group = 'stack'
    dset = h5py.File(fn, 'r')
    return array(dset[group])

def write_image_stack(npy_vol, fn, **kwargs):
    fn = os.path.expanduser(fn)
    if fn.endswith('.png'):
        write_png_image_stack(npy_vol, fn, **kwargs)
    elif fn.endswith('.h5'):
        write_h5_stack(npy_vol, fn, **kwargs)
    elif fn.endswith('.npy'):
        write_npy_image_stack(npy_vol, fn, **kwargs)
    else:
        raise ValueError('Image format not supported: ' + fn + '\n')


def write_png_image_stack(npy_vol, fn, **kwargs):
    if numpy.max(npy_vol) < 2**16:
        mode = 'I'
        npy_vol = uint16(npy_vol)
    else:
        mode = 'RGBA'
        npy_vol = uint32(npy_vol)
    for z in range(npy_vol.shape[2]):
        Image.fromarray(npy_vol[:,:,z], mode).save(fn % z)

def write_h5_stack(npy_vol, fn, **kwargs):
    if not kwargs.has_key('compression'):
        kwargs['compression'] = None
    if not kwargs.has_key('chunks'):
        kwargs['chunks'] = None
    try:
        group = kwargs['group']
    except KeyError:
        group = 'stack'
    fout = h5py.File(fn, 'w')
    fout.create_dataset(group, data=npy_vol, **kwargs)
