
from PIL import Image
import numpy as np
from scipy.misc import imread, imsave
import cv2
from scipy import ndimage as ndi
from skimage.morphology import medial_axis
from scipy.io import savemat,loadmat
#import skimage.io as io
"load image data"

def getDepth(filename):
    path='..//images//depth.rmf'+filename
    f = open( path,'rb')

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
    elif TypeNum==1:
	DataType=np.double
    elif Type==2:
	DataType=np.unit8
    else:
	DataType=np.unit8
    while j<columns:
	i=0
	while i<rows:
	    raw[i,j]=np.fromfile(f, DataType, 1)
	    i=i+1
	j=j+1
    f.close()
    r1=int(rows*5.86/9)
    c1=int(columns*7.5/9)

    im=np.array(raw)
    print r1,c1
#im = np.array(raw * 255, dtype = np.uint8)
    im=cv2.resize(im,(c1,r1),interpolation=cv2.INTER_AREA)
    print im.shape

    savemat('../data/depth.mat',{'d':im})
    return im

##fw = open( 'data//depth.txt','w')
##
##for j in range(0, c1-1) :
##    for i in range(0, r1-1):
##        fw.write(str(im[i,j]))
##        fw.write(",")
##    fw.write("\n")
##fw.close
print "finish"
##i=1
##while i<10:
##    kernel = np.ones((2,2),np.uint8)
##    im = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
##    i=i+1
##cv2.imwrite('2.jpg',im)
##cv2.imshow('raw data',im)
##cv2.waitKey(0)
##
