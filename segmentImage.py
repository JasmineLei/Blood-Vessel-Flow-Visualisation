###########################################################################
## This file is for segementing image using SimpleITK.
###########################################################################
import SimpleITK as sitk
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage.morphology import remove_small_objects, binary_closing
from skimage.filters import threshold_otsu, rank
import cv2
from profilehooks import profile,timecall

#@profile(immediate=True)
def segment_Image(im,depth):
    
    ## Setting lower threshold using Otsu method.
    thresh_l = 0.8*threshold_otsu(im)
    print thresh_l
    img = sitk.GetImageFromArray(im)

    ## Smoothing image.  
    imgSmooth = sitk.CurvatureFlow(image1=img,
                                    timeStep=0.125,
                                    numberOfIterations=10)
    lstSeeds=[]

    for i in range(0, im.shape[1]-1, 10 ):
        for j in range (0, im.shape[0]-1, 10 ):
            if im[j][i]>0:
             seed = [int(i), int(j)]
             lstSeeds.append( seed )
    
    ## Segmenting image.
    imgWhiteMatter = sitk.ConnectedThreshold(image1=imgSmooth, 
                                              seedList=lstSeeds, 
                                              lower=thresh_l, 
                                              upper=255,
                                              replaceValue=255)
    nda = sitk.GetArrayFromImage(imgWhiteMatter)
    
    nda.astype(bool)
    nda1=remove_small_objects(nda,150,connectivity=3)
    nda1.astype(int)
    newdepth = depth
    
    return nda1,newdepth


