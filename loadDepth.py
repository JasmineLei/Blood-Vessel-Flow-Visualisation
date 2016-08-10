###########################################################################
## This file is for loading depth data, similar to showImage.py.
###########################################################################
from PIL import Image
import numpy as np
from scipy.misc import imread, imsave
import cv2
from scipy import ndimage as ndi
from click_crop import showCropWindow
import csv

#import skimage.io as io
"load image data"
LEVEL=20
def load_Depth(filename,refPt,im):
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
    print "depth data:",DataType
    while j<columns:
        i=0
        while i<rows:
            raw[i,j]=np.fromfile(f, DataType, 1)

            i=i+1
        j=j+1
    f.close()
    r1=int(rows*5.86/7)
    c1=int(columns*7.5/7)


    depthMAT_total = np.array(raw, dtype = DataType)
    depthMAT_total=cv2.resize(depthMAT_total,(c1,r1),interpolation=cv2.INTER_NEAREST)    

    if refPt!=None:
        depthMAT=np.zeros([im.shape[0],im.shape[1]])

        startx=refPt[0][0]
        starty=refPt[0][1]
        endx=refPt[1][0]
        endy=refPt[1][1]

        di1=0
        for di in range(startx,endx-1):
            dj1=0
            for dj in range(starty,endy-1):
                depthMAT[dj1][di1]=depthMAT_total[dj][di]
                dj1+=1
            di1+=1
    else:
        depthMAT=depthMAT_total

      
 
        
    depthMAT= setRange(depthMAT)

    while i<10:
         kernel = np.ones((2,2),np.uint8)
         depthMAT = cv2.morphologyEx(depthMAT, cv2.MORPH_OPEN, kernel)
         i=i+1

   
    return depthMAT


def setRange(depthMAT,unit=1000):
    while depthMAT.max()>unit:
        depthMAT=depthMAT/10
    return depthMAT
    
