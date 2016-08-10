###########################################################################
## This file is for skeletonising image using skimage.
###########################################################################
import numpy as np
from skimage.morphology import skeletonize, remove_small_objects, binary_closing


from skimage import img_as_ubyte

def skeletonize_Image(im):
    im1=np.array(im.size)
    for i in range(0,4):
        im1 = binary_closing(im)
    im1.astype(bool)
    nda1=remove_small_objects(im1,150,connectivity=2)
    nda1.astype(int)
    skel1 = skeletonize(nda1)
    skel = img_as_ubyte(skel1)
    return skel
