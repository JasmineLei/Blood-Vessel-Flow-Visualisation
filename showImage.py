###########################################################################
## This file is for showing input image based on the SaveToRMF.m file.
###########################################################################
import numpy as np
import cv2
from click_crop import showCropWindow
import csv
#import skimage.io as io
"load image data"

def load_Image(filename):
    f = open( filename,'rb')
    f.seek(8,0)
    TypeNum=int(f.read(1))
    f.seek(1,1)
    dimension=f.read(1)
    f.seek(1,1)
    rows=int(f.read(5))
    f.seek(1,1)
    columns=int(f.read(5))
    f.seek(1,1)
    slices=int(f.read(5))
    f.seek(1,1)
    raw=np.zeros((rows,columns))
    i=0
    j=0
    if TypeNum==0:
        DataType=np.single
    else:
        if TypeNum==1:
            DataType=np.dtype('f8')
        else:
            if TypeNum==2:
                DataType=np.unit8
            else:
                DataType=np.unit8
    print "image data:",DataType
    while j<columns:
        i=0
        while i<rows:
            raw[i,j]=np.fromfile(f, DataType, 1)
            i=i+1
        j=j+1
    f.close()
    r1=int(rows*5.86/7)
    c1=int(columns*7.5/7)

    im = np.array(raw * 255, dtype = np.uint8)
    im=cv2.resize(im,(c1,r1),interpolation=cv2.INTER_AREA)
    i=1
          
    
    ref=None
#    ref,im_cropped=showCropWindow(im)  ## comment this if you want to simulate global flow
    im_cropped=im.copy()
    while i<10:
        kernel = np.ones((2,2),np.uint8)
        im_cropped = cv2.morphologyEx(im_cropped, cv2.MORPH_OPEN, kernel)   # noise removal
        i=i+1
        
        
    return ref,im_cropped


