###########################################################################
## This file is for connecting breakpoints and smoothing depth data.
###########################################################################
import numpy as np
from PIL import Image

import cv2
import SimpleITK as sitk

from scipy import ndimage

import math

from profilehooks import profile,timecall
import csv
LEVEL=5
FILL_PIXEL=1
VISITED_PIXEL=1



def Neigh_Cov(im):
    ###########################################################################
    ## Getting neibourhood info using convolution.
    ###########################################################################
    k_n=np.array([[1,1,1],[1,1,1],[1,1,1]])
    return ndimage.convolve(im,k_n,mode='constant',cval=0.0)



def fillPixel(i,j,convalue_n):
    ###########################################################################
    ## Processing pixels on the vessel (foreground).
    ###########################################################################
    global im,endpoint,current_depth,rows,cols,rough_range
    global enableComplexSmooth,depthMAT
    rows=im.shape[0]
    cols=im.shape[1]


    im[j][i]=VISITED_PIXEL
            
    if depthMAT[j][i]<=0:
        depthMAT[j][i]=rough_range

            

    current_depth=depthMAT[j][i]   
    if 1<convalue_n[j][i]<=3:

        if convalue_n[j][i]==2:
        
            [i1,j1],dif_dep=checkConnectivity(i,j,convalue_n)
            
            if dif_dep<=4*rough_range:
                 connectEndPoints(i,j,i1,j1)
                 
        SimpleSmoothDepth(i,j)
        
    if enableComplexSmooth==True:
            ComplexSmoothDepth(i,j)

        
    
        
def ComplexSmoothDepth(i,j):
    ###########################################################################
    ## Processing pixels in the intersection.
    ###########################################################################
    global depthMAT,rough_range
    
    diff=5*rough_range
    current_d=depthMAT[j][i]
    temp=depthMAT[j][i]
    
    x=-1
    y=-1
    while x<2:
        while y<2:
            if depthMAT[j+y][i+x]>0 and int(depthMAT[j+y][i+x])== depthMAT[j+y][i+x] and x!=0 or y!=0:
                ele=depthMAT[j+y][i+x]
            
                if ele!=0 and math.fabs(ele-current_d)<=diff:            
  
                    diff=math.fabs(ele-current_d)
                    temp=ele

            y+=1
        x+=1

    depthMAT[j][i]=int(temp)


def SimpleSmoothDepth(i,j):
    ###########################################################################
    ## Processing pixels in single vessels.
    ###########################################################################
    global depthMAT,rough_range
    global modified_depthMAT,mask_depthMAT
    
    SimpleCase_neighborhood=np.copy(depthMAT[j-1:j+2,:][:,i-1:i+2])
    if SimpleCase_neighborhood[SimpleCase_neighborhood>0].shape[0]>0 and SimpleCase_neighborhood.shape[1]>0:
        SimpleCase_n_max=np.nanmax(SimpleCase_neighborhood)
        SimpleCase_n_median=np.median(SimpleCase_neighborhood[SimpleCase_neighborhood>0])
        SimpleCase_n_min=np.nanmin(SimpleCase_neighborhood[SimpleCase_neighborhood>0])
        SimpleCase_n_mean=np.mean(SimpleCase_neighborhood[SimpleCase_neighborhood>0])
        if SimpleCase_n_max == SimpleCase_n_median:
            SimpleCase_n_median = SimpleCase_n_min
        count=3
        if SimpleCase_n_max-SimpleCase_n_min>0.5*rough_range:
            newvalue=SimpleCase_n_median
            depthMAT[j-1:j+2,:][:,i-1:i+2][depthMAT[j-1:j+2,:][:,i-1:i+2]>0]=int(newvalue)
            
            
        else:
            x=depthMAT[j][i]
            depthMAT[j][i] = int(x)

    
      

def checkConnectivity(i,j,convalue_n):
    ###########################################################################
    ## checking potential connection.
    ###########################################################################
    global im
    
    neighbor_im=np.copy(im[j-1:j+2,i-1:i+2])
    loc=np.nonzero(neighbor_im)
    conPoint=[i,j]
    dep=300.0
    if len(loc)>0 and len(loc[0]>0):
        
        if loc[0][0]!=i or loc[1][0]!=j:
            nz_i=loc[0][0]
            nz_j=loc[1][0]
        else:
            nz_i=loc[0][1]
            nz_j=loc[1][1]
        

        if nz_i==0:
            if nz_j==1:
                dep,conPoint=UpCase(i,j)

            elif nz_j==0:
                dep,conPoint=UpLeftCase(i,j)

            else:
                dep,conPoint=UpRightCase(i,j)

        elif nz_i==1:
            if nz_j==0:
                dep,conPoint=LeftCase(i,j)

            elif nz_j==2:
                dep,conPoint=RightCase(i,j)

        else:
            if nz_j==0:
                dep,conPoint=DownLeftCase(i,j)

            elif nz_j==1:
                dep,conPoint=DownCase(i,j)

            else:
                dep,conPoint=DownRightCase(i,j)

    
    return conPoint,dep

###########################################################################
## Different cases for searching area.
###########################################################################
def UpCase(i,j):
    start_i=i-4
    end_i=i+5
    start_j=j
    end_j=j+9

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)

def UpLeftCase(i,j):
    start_i=i
    end_i=i+9
    start_j=j
    end_j=j+9

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)
        
def UpRightCase(i,j):
    start_i=i-8
    end_i=i+1
    start_j=j
    end_j=j+9

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)    
    
def LeftCase(i,j):
    start_i=i
    end_i=i+9
    start_j=j-4
    end_j=j+5

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)

def RightCase(i,j):
    start_i=i-8
    end_i=i+1
    start_j=j-4
    end_j=j+5

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)

def DownRightCase(i,j):
    start_i=i-8
    end_i=i+1
    start_j=j-8
    end_j=j+1

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)

def DownLeftCase(i,j):
    start_i=i
    end_i=i+9
    start_j=j-8
    end_j=j+1

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)

def DownCase(i,j):
    start_i=i-4
    end_i=i+5
    start_j=j-8
    end_j=j+1

    return getConnectedPoint(i,j,start_i,start_j,end_i,end_j)


def getConnectedPoint(i,j,start_i,start_j,end_i,end_j):
    ###########################################################################
    ## Connecting breakpoints.
    ###########################################################################
    global rows,cols
    global depthMAT
    dif_dep=np.amax(depthMAT)
    target_i=i
    target_j=j
    
    u_j=start_j
    while u_j<end_j:
        u_i=start_i
        while u_i<end_i:
            if u_j!=j or u_i!=i:
                u_i0=min(cols-1,u_i)
                u_j0=min(rows-1,u_j)
                d=float(depthMAT[u_j0][u_i0]-depthMAT[j][i])
            
                if im[u_j0][u_i0]==1 and dif_dep>abs(d):
                    dif_dep=abs(d)
##                print 'current Min dep:',dif_dep
                    target_i=u_i0
                    target_j=u_j0
            u_i+=1
        u_j+=1

    return dif_dep,[target_i,target_j]



def connectEndPoints(i,j,i1,j1):
    global im,current_depth,depthMAT
    
    cv2.line(im,(i,j),(i1,j1),2)
    c_j=min(j,j1)
    while c_j <=max(j,j1):
        c_i=min(i,i1)
        while c_i <=max(i,i1):

            if im[c_j][c_i]==2:
                im[c_j][c_i]=1
                depthMAT[c_j][c_i]=current_depth
            c_i+=1
        c_j+=1

    
    

@profile(immediate=True)
def moveObject(initial_depthMAT):
    ###########################################################################
    ## Checking each pixel and invoking functions to process pixels on the vessels.
    ###########################################################################
    global done,startx,starty,clock,screen,endx,endy
    global im
    global endpoint
    global current_depth
    global depthMAT
    global rough_range
    global modified_depthMAT,mask_depthMAT
    
    if np.amax(im)!=1:
        ret,im = cv2.threshold(im, 250, 1, cv2.THRESH_BINARY)
    else:
        print np.amax(im)
        np.int8(im)
    mask_depthMAT=initial_depthMAT
    modified_depthMAT=initial_depthMAT
    depthMAT=getDepth(im,modified_depthMAT)
    rough_range=np.median(depthMAT[depthMAT>0])/LEVEL
    im0=np.copy(im)

    convalue_n=Neigh_Cov(im0)

    cols=im.shape[1]
    rows=im.shape[0]

    for y in range(0,rows,1): 
        for x in range(0,cols,1):
            if im[y][x]==1:
                fillPixel(x,y,convalue_n)

    return convalue_n
    
    

def getDepth(im0,initial_depth):
    if FirstIter!=False:
        depthMAT_total=im0*initial_depth
#        fl = open('../images/skeldepth1.csv', 'w')
#
#        writer = csv.writer(fl)
#        for values in depthMAT_total:
#            writer.writerow(values)
#
#        fl.close()
    else:
        depthMAT_total=t_depth

    return depthMAT_total
    
def connectSkeleton(im0,refPt,initial_depth,depth,ComplexSmooth=False):
    global done,screen
    global startx,starty,clock
    global window_width,window_height
    global im
    global endx,endy
    global depthMAT
    global enableComplexSmooth,FirstIter
    global t_depth
    
    if ComplexSmooth==True:
        enableComplexSmooth=True
    else:
        enableComplexSmooth=False
    
    if np.array_equal(initial_depth,depth):
        FirstIter=True
    else:
        FirstIter=False
        t_depth=depth
    
        
    im=np.copy(im0)
    convalue_n=moveObject(initial_depth)

    return im,depthMAT,modified_depthMAT,convalue_n
    
    


    
    
