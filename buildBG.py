
import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
#from scipy.io import savemat,loadmat
from PIL import Image
import pygame
from skeletonizeImage import skeletonize_Image

MASK_RANGE=1
LEVEL=5
def reconstructVessels(im,skeldepth,skel,convalue_n):
    global depthrange,skel_dis
    
    depthrange=np.mean(skeldepth[skeldepth>0])/LEVEL
    distance = ndimage.distance_transform_cdt(im , return_distances=True)
    skel_dis= skel * distance

    #savemat('..//data//skel_dis.mat',{'skel_dis':skel_dis})
    
    binary_ves,depth=buildVessels(skel,skeldepth,convalue_n)
#    colored_ves=skel_dep,binary_ves)
    
    return binary_ves,depth
    
    
    
    
    
    
def buildVessels(skel,skeldepth,convalue_n):
    global skel_dis
    mask_num = int(int(skel_dis.max()/MASK_RANGE)+1)
    
    
    rows,cols = skel.shape
    
    np.set_printoptions(threshold='nan')
#    print skel_dis
    struct = ndimage.generate_binary_structure(2, 1)
    
    for mask_index in range(0,mask_num):    
        
        mask_thresh_h=MASK_RANGE*(mask_index+1)
        skel_mask=np.copy(skel)
  
        
        for i in range(0,rows):
            for j in range(0,cols):
                if skel_mask[i][j]>0 and skel_dis[i][j] >=  mask_thresh_h:
                    skel_mask[i][j]=0

                

        if mask_index==0:
            skel_dilated=np.copy(skel)
 
        else:    
            skel_mask=ndimage.binary_dilation(skel_mask,structure=struct,iterations=3)                   
            skel_dilated=np.logical_or(skel_dilated,skel_mask)

#        

    new_vessel=np.int8(skel_dilated)
    distance = ndimage.distance_transform_cdt(new_vessel , return_distances=True)
    skel_dis= skel * distance  
    new_depth=updateDepth(new_vessel,skeldepth,convalue_n)
    new_depth=updateDepth(new_vessel,skeldepth,convalue_n,newdepth=new_depth)
    return new_vessel,new_depth

def updateDepth(vessel,depthMAT,convalue_n,newdepth=None):
    global depthrange,skel_dis
    
    print 'largest distance: ',skel_dis.max()
    rows = depthMAT.shape[0]
    cols= depthMAT.shape[1]
    count = 0
    lastDepth=0

    if newdepth is None:
        modified_depthMAT=np.zeros((rows,cols))
        for j in range(1,rows-1):
            for i in range(1,cols-1):
                
                if 0<convalue_n[j][i]<=3:
                    if count >0 and abs(depthMAT[j][i]-lastDepth)<=depthrange:
                        count-=1
                        continue
                    g=np.zeros((3,3))
                    d=-1
                    while d<2:
                        c=-1
                        while c<2:
                            g[d+1][c+1]=depthMAT[j+d][i+c]
                            c+=1
                        d+=1
                        rangeX = 1*skel_dis[j][i]
                        rangeY = 1*skel_dis[j][i]
                        if g[0][1] > 0 or g[2][1] > 0:
                            rangeX = 2
                    
                        if g[1][0] > 0 or g[1][2] > 0:
                            rangeY = 2

                            
#                    
#                    perpendicular_depth= np.rot90(g)
#                    
#                    b_d = modifySize(perpendicular_depth,i,j)
    #                print 'small: ',perpendicular_depth
    #                print 'large: ',b_d
                #    modified_depthMAT[j][i]=0;
    #                a_d=np.repeat(perpendicular_depth,5,1)
    #                b_d=np.repeat(a_d,5,0)
                   
        #            print 'b_d: ',b_d
                #    print modified_depthMAT[j-4:j+5,:][:,i-4:i+5]
                #    if modified_depthMAT[j-4:j+5,:][:,i-4:i+5].shape[0]==9 and modified_depthMAT[j-4:j+5,:][:,i-4:i+5].shape[1]==9:
                #    modified_depthMAT[j-4:j+5,:][:,i-4:i+5][modified_depthMAT[j-4:j+5,:][:,i-4:i+5]==0]=modified_depthMAT[j-4:j+5,:][:,i-4:i+5]+b_d[0:modified_depthMAT[j-4:j+5,:][:,i-4:i+5].shape[0],0:modified_depthMAT[j-4:j+5,:][:,i-4:i+5].shape[1]]
#                    n_range=skel_dis[j][i]    
                    x=-(rangeX-1)
                    count = min(rangeX,rangeY)
                    while x<rangeX and j+x<vessel.shape[0]:
                       y=-(rangeY-1)
                       while y<rangeY and i+y<vessel.shape[1]: 
    
                           if vessel[j+x][i+y]>0 and modified_depthMAT[j+x][i+y]==0:
                               modified_depthMAT[j+x][i+y]=np.amax(g)
                               lastDepth = modified_depthMAT[j+x][i+y]
                           y+=1
                       x+=1
                       
    else:
        modified_depthMAT=newdepth
        for j in range(1,rows-1):
            for i in range(1,cols-1):
                if convalue_n[j][i]>0:
                    x=-10
                    while x<11 and j+x<rows:
                        y=-10
                        while y<11 and i+y<cols:
                            if modified_depthMAT[j+x][i+y]==0 and vessel[j+x][i+y]>0:
                                 modified_depthMAT[j+x][i+y]= depthMAT[j][i]
                            y+=1
                        x+=1
    return modified_depthMAT

def modifySize(p_depth,i,j):
    distance=skel_dis[j][i]
    size = 2 * distance+1
    new_p_depth=np.zeros((size,size))
    nonzero_index=np.nonzero(p_depth)
    for c in range(0,len(nonzero_index[0])):
        if nonzero_index[0][c] == 0:
            if nonzero_index[1][c] == 0:
                drawType='lt'
                
            elif nonzero_index[1][c] == 1:
                drawType='t'
          
            else:
                drawType='rt'
            
        elif nonzero_index[0][c] == 1:
            if nonzero_index[1][c] == 0:
                drawType='l'
               
            elif nonzero_index[1][c] == 1:
                drawType='itself'
                
            else:
                drawType='r'
        else:
            if nonzero_index[1][c] == 0:
                drawType='lb'
 
            elif nonzero_index[1][c] == 1:
                drawType='b'
  
            else:
                drawType='rb'
        new_p_depth=fillNewArray(new_p_depth,p_depth[1][1],distance,drawType)
        
    return new_p_depth


def fillNewArray(new_p_depth,depth,distance,drawType):
    if drawType != 'itself':
        
        if 'l' in drawType:
            diagonal=True
            x_start=0
            x_stop=distance
            if drawType == 'lt':
                y_start=0
                y_stop=distance
            elif drawType == 'l':
                diagonal=False
                y_start=distance
                y_stop=distance
            else:
                y_start=distance
                y_stop=2*distance
        elif 'r' in drawType:
            diagonal=True
            x_start=distance
            x_stop=2*distance
            if drawType == 'rt':
                y_start=0
                y_stop=distance
            elif drawType == 'r':
                diagonal=False
                y_start=distance
                y_stop=distance
            else:
                y_start=distance
                y_stop=2*distance
        elif drawType == 't':
            diagonal=False
            x_start=distance
            x_stop=distance
            y_start=0
            y_stop=distance
        elif drawType == 'b':
            diagonal=False
            x_start=distance
            x_stop=distance
            y_start=distance
            y_stop=2*distance

        for x_index in range(x_start,x_stop+1):
            for y_index in range(y_start,y_stop+1):
                if x_index==x_start and y_index==y_start or x_index==x_stop and y_index==y_stop:
                    new_p_depth[y_index][x_index]=-1
                if diagonal==False:
                    new_p_depth[y_index][x_index]=depth
                else:
                    if abs(y_index-distance) == abs(x_index-distance):
                        new_p_depth[y_index][x_index]=depth
    return new_p_depth


def scaleImage(path_img, dilated_img, depth, color_depth, scale=1):
                  
        final_vessel = ndimage.zoom(dilated_img, scale, order=0) 
        final_path = skeletonize_Image(255*ndimage.zoom(path_img, scale, order=0))/255# use nearest neighbour
        final_depth = final_path*ndimage.zoom(depth, scale, order=0)
        final_color_depth = ndimage.zoom(color_depth, scale, order=0)

        return final_path,final_vessel,final_depth, final_color_depth
