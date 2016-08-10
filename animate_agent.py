###########################################################################
## This file is for animating blood flow using Pygame.
###########################################################################
import pygame
from pygame.locals import *
import numpy as np
import random
from scipy import ndimage
import time
from skimage.filters import roberts
import copy
import os
import sys
import math
from tkMessageBox import *
import csv


#from scipy.io import savemat,loadmat
from writeResult import recordSingle,recordBranch
from profilehooks import profile,timecall

x = 100
y = 0
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

LEVEL=5
SPLIT_RANGE=20
FILL_PIXEL=1
INTERVAL=5
MAX_TRIALS=25
RADIUS=6
NEIGHBOR_SIZE=2


class FlowAgent(pygame.sprite.Sprite):
    ###########################################################################
    ## Flow particles.
    ###########################################################################
    PathFlag=None;

    def __init__(self,group, Id, x, y, isclick, flag, basicDirection=[-1,-1]):
        
        #super(pygame.sprite.Sprite).__init__()
        pygame.sprite.Sprite.__init__(self)
        # Set the background color and set it to be transparent
        self.Id=Id
        self.group=group
        self.x=x
        self.y=y
        self.branch=0
        self.basicDirection=basicDirection
        self.vessel_width = 2*self.getMeanNeighborhoodDistance(self.x,self.y)
        self.objectsize = int(1.2 * self.vessel_width)
        
        self.image = pygame.surfarray.make_surface(np.zeros((1.2*self.objectsize,1.2*self.objectsize))).convert()
        self.rotated = 0
        self.image.fill((0,0,0))
        self.image.set_colorkey((0,0,0))
        
        
        #self.image= pygame.image.load('../images/cell2.jpg')
        #self.image=pygame.transform.scale(pygame.image.load('../images/cell2.png'),(self.vessel_width, self.vessel_width))
#        self.flag = float(flag)
        self.flag = self.getFlag(isclick,flag)
        
        self.searchTrials=MAX_TRIALS
        self.hide=False
        self.current_depth=0
        self.last_depth=0
        
        
#        self.visit(self.x,self.y,self.flag)
        if self.basicDirection[0]!=-9:
            self.setInitialDirection(self.basicDirection, x, y)
        self.visit(self.x,self.y,self.flag)
    
        self.current_depth=animateFlow.depthMAT[self.y][self.x]
        self.last_depth=animateFlow.depthMAT[self.y][self.x]
        self.color = self.getColor(self.current_depth)
        self.rect = self.image.get_rect()
        self.rect.x = x-self.objectsize/2
        self.rect.y = y-self.objectsize/2
        self.drawMovingObject()
        

        self.group.Num+=1
        self.group.agentsIds+=1
        
        self.split=True


    def getColor(self,depth):
        ###########################################################################
        ## Changing particla colour according to depth.
        ###########################################################################
        level = depth/animateFlow.depth_range
        a = 255 - int(level*255/(5*LEVEL))
        color = (a,180,120,255)
        return color
    
    def getFlag(self,isclick,oldflag):
        ###########################################################################
        ## Updating flag value.
        ###########################################################################
        if isclick == True and FlowAgent.PathFlag[self.y][self.x]>1:
            fraction = FlowAgent.PathFlag[self.y][self.x] - int(FlowAgent.PathFlag[self.y][self.x])
            flag = int(FlowAgent.PathFlag[self.y][self.x])/100 + fraction + (1-fraction)*0.1
            d1 = (int(FlowAgent.PathFlag[self.y][self.x])%100)/10
            d2 = (int(FlowAgent.PathFlag[self.y][self.x])%100)%10
            self.basicDirection = [d1,d2]
        else:
            flag = oldflag
        return flag
 
    def drawMovingObject(self):
        ###########################################################################
        ## Drawing moving particle.
        ###########################################################################
        #print "draw flow"
        i = self.x
        j = self.y

        
        startx=self.x-int(self.objectsize*0.5)
        starty=self.y-int(self.objectsize*0.5)
        pygame.draw.circle(self.image, self.color, (int(self.objectsize*0.5), int(self.objectsize*0.5)), int(self.objectsize*0.5))
        height=self.image.get_height()
        width=self.image.get_width()
        for i in range(0,height):
            for j in range(0,width):
                if startx+i < animateFlow.backgroundMatrix.shape[0] and starty+j < animateFlow.backgroundMatrix.shape[1]:
                    if animateFlow.backgroundMatrix[startx+i][starty+j]<1:
                        self.image.set_at((i,j),(0,0,0,255))
                    if self.current_depth - animateFlow.depth_range>animateFlow.color_depthMAT[starty+j][startx+i] or animateFlow.color_depthMAT[starty+j][startx+i]>=self.current_depth + 1.5* animateFlow.depth_range:
                        self.image.set_at((i,j),(0,0,0,255))

        
        return
    def rot_center(self, image, angle):
        """rotate an image while keeping its center and size"""
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        return rot_image    
        
    
    def setInitialDirection(self, direction, x, y):
        ###########################################################################
        ## Setting initial direction for particles.
        ###########################################################################
        stepX=direction[0]
        stepY=direction[1]
        if y+stepY < animateFlow.window_height and x+stepX < animateFlow.window_height:
            if animateFlow.im[y+stepY][x+stepX]>0:
                self.x=x+stepX
                self.y=y+stepY
                #print "good position!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            elif animateFlow.im[y][x+stepX]>0:
                self.x=x+stepX
                self.y=y
            elif animateFlow.im[y-stepY][x+stepX]>0:
                self.x=x+stepX
                self.y=y-stepY
            elif stepX!=0:
                if animateFlow.im[y-stepY][x]>0:
                    self.x=x
                    self.y=y-stepY
                elif animateFlow.im[y+stepY][x]>0:
                    self.x=x
                    self.y=y+stepY
            self.basicDirection = [self.x-x,self.y-y]
        
#        self.flag=self.flag+100/animateFlow.depthMAT[self.y][self.x]
            
    def getMeanDepth(self,former,latter,current):
        if former==0.0 and latter==0.0:
            return np.nanmax(animateFlow.depthMAT)+1+current
        elif former==0.0:
            return latter
        elif latter==0.0:
            return former
        else:
            return float(former+latter)/2.0



    def handleIntersection(self, nextPixel,branches,convalue_n):
        ###########################################################################
        ## Handling splitting situation.
        ###########################################################################
        self.group.Num+=1
        row=-2
        
        findNext=0
        
        while row<2 and nextPixel[1]+row < animateFlow.window_height and findNext==0:
            row+=1
            col=-2
            while col<2 and nextPixel[0]+col < animateFlow.window_width and findNext==0:
                col+=1

                if animateFlow.im[nextPixel[1]+row][nextPixel[0]+col]==1 and self.checkFlag(nextPixel[0]+col,nextPixel[1]+row): #currentFlag==1.0 or 
                    if 2<convalue_n[nextPixel[1]+row][nextPixel[0]+col] and self.split == True:
                        findNext=1
                        newAgent = FlowAgent(self.group,self.group.agentsIds , nextPixel[0]+col, nextPixel[1]+row, 0, self.flag,[col,row])
                        if self.hide == True:
                            self.split = False
                            newAgent.split = False
                            newAgent.current_depth = self.current_depth
                        self.group.add(newAgent)
                        for group in animateFlow.groups:
                            if group!=newAgent.group and abs(group.depth-newAgent.current_depth)<animateFlow.depth_range:

                                 if pygame.sprite.spritecollideany(newAgent, group, pygame.sprite.collide_rect_ratio(0.5)):
                                     newAgent.group.Num-=1

                                     newAgent.kill()
                                     newAgent=None
                                     break

                        break

        return
    
    def checkFlag(self,x,y):
        if FlowAgent.PathFlag[y][x]>0:
#            print "check ",x,y,FlowAgent.PathFlag[y][x],self.flag
            visitedGroup=int(FlowAgent.PathFlag[y][x])/100
            visitedDirection = int(FlowAgent.PathFlag[y][x])%100
            visitedDirectionX = visitedDirection/10
            visitedDirectionY = visitedDirection%10
            currentGroup=int(self.flag)
            if FlowAgent.PathFlag[y][x]==1.0:
                    return True
            elif visitedGroup!=currentGroup:
#                return True
                if 0<animateFlow.con_N[y][x]<=3:
                    if self.current_depth-animateFlow.depth_range < animateFlow.depthMAT[y][x] <= self.current_depth+1.5*animateFlow.depth_range:
#                        currentDirection = self.basicDirection[0]*10+self.basicDirection[1]
                        if self.basicDirection[0]+visitedDirectionX ==3 and self.basicDirection[1]+visitedDirectionY==3:
#                            print 'come here1!!!'
                            return False
                        else:
#                            print 'come here2!!!'
                            return True
                    else:
#                        print 'come here3!!!'
                        return True
                else:
                    if FlowAgent.PathFlag[y][x] != 0:
                        if self.basicDirection[0] != visitedDirectionX  and self.basicDirection[1] != visitedDirectionY:
                            return False
                    return True
            else:
                visitedFlag=float(str(FlowAgent.PathFlag[y][x]-int(FlowAgent.PathFlag[y][x])))
                currentFlag=float(str(self.flag-int(self.flag)))
                if currentFlag>visitedFlag:
#                    print 'come here4!!!'
                    return True
                else:
#                    print 'come here5!!!'
#                    print visitedFlag,'   ',currentFlag,' ',x,y
                    return False
        
        else:
#            print 'come here6!!!'
            return False
    
    def newFlag(self,flag):
        currentFlag=float(str(flag-int(flag)))
        return flag+currentFlag*1.00000001
        
    def updateDirection(self,nextX,nextY):
        if nextX < self.x:
            x = 1-nextX
        else:
            x = nextX
        if nextY < self.y:
            y = 1-nextY
        else:
            y = nextY
        self.basicDirection = [x,y]

    def visit(self,x,y,value):

        if 1==1:
            v_group = int(value)
            pixel_flag = v_group*100+self.basicDirection[0]*10+self.basicDirection[1]
            pixel_flag = pixel_flag + (value - v_group)
            FlowAgent.PathFlag[y][x] = pixel_flag

        return
        
    def getMeanNeighborhoodDistance(self,x,y):
        neighborhood=animateFlow.distance[y-2:y+2,:][:,x-2:x+2]
        if len(neighborhood):
            value = neighborhood.mean()
        else:
            value = 0
        return value
        

    def checkNextPixel(self,x,y,count,p,record,depthArray,depthMAT,im):
        if im[y][x]>0 and self.searchTrials>0 and self.checkFlag(x,y):
            record=-p
            count+=1
            depthArray=depthMAT[y][x]+depthArray
            if self.current_depth-animateFlow.depth_range < depthMAT[y][x] <= 1.5*self.current_depth+animateFlow.depth_range:
                self.hide=False
                if self.searchTrials<MAX_TRIALS and math.fabs(p)<=1:
                    self.searchTrials=MAX_TRIALS

        return count,depthArray,record
    
    def update(self):
        self.vessel_width = self.getMeanNeighborhoodDistance(self.x,self.y) 
        #print 'vessel_width: ',self.vessel_width
        speed=0



        speed=math.floor(animateFlow.width_ave/self.vessel_width)
  
        update_count=0
        while(update_count<=speed):
            tempx=self.x
            tempy=self.y

            if self.searchTrials >= MAX_TRIALS-1:
                self.visit(self.x,self.y,self.flag)
            self.x, self.y= self.getNextPixel(self.x,self.y,animateFlow.con_R,animateFlow.con_L,animateFlow.con_V,animateFlow.con_H,animateFlow.con_N,animateFlow.depthMAT)
            
            if self.x!=tempx or self.y!=tempy:
                
                self.rect.x= self.x-self.objectsize/2
                self.rect.y= self.y-self.objectsize/2
        
                
                self.drawMovingObject()
            else:
                self.group.Num-=1

                if self.group.Num==0:
                    self.group.empty()
                    animateFlow.groups.remove(self.group)
                    self.group=None

                self.kill()
                self=None
                break
                
            update_count+=1 


        

    def getNextPixel(self, i,j,convalue_rd,convalue_ld,convalue_v,convalue_h,convalue_n,depthMAT_input):
        ###########################################################################
        ## Getting next position.
        ###########################################################################
        global neighbor_depth
        former_depth1=0.0
        latter_depth1=0.0
        former_depth2=0.0
        latter_depth2=0.0
        former_depth3=0.0
        latter_depth3=0.0
        former_depth4=0.0
        latter_depth4=0.0
        nextPixel=[i,j]
        nextPixel0=[i,j]
        depthMAT=depthMAT_input
        
        im=animateFlow.im
        rows=im.shape[0]
        cols=im.shape[1]
        
        max_depth=np.max(animateFlow.depthMAT)+1
        neighbor_depth=[max_depth,max_depth,max_depth,max_depth]
        start=[0,0,0,0]
        stop=[0,0,0,0]
        direction=-1
        endpoint=False

        f_count=0
        l_count=0
   
        
        self.hide=True        
        
        if self.searchTrials==MAX_TRIALS:
            if math.fabs(self.current_depth-depthMAT[j][i])<animateFlow.depth_range:
                self.current_depth=depthMAT[j][i]
              
        elif self.searchTrials==0:
            return nextPixel

        
        if convalue_n[j][i]==3:
            conX=-1
            conY=-1
            found=0
            while conX<=1 and found==0:
                conY=-1
                while conY<=1 and found==0:
                    if conX!=0 or conY!=0:
                        if im[j+conY][i+conX]==1:
                            if self.checkFlag(i+conX,j+conY):
#                                print 'oooooooo'
                                nextPixel0[0]= i+conX
                                nextPixel0[1]= j+conY
                                found=1
                    conY+=1
                conX+=1
            
            if found==0:
                endpoint=True
                
        if convalue_n[j][i]<3:

            if animateFlow.testType == 1 and convalue_n[j][i] == 2:
                animateFlow.sCount+=1
                if animateFlow.sCount == 1:
                    recordSingle()
                    animateFlow.running = 0
                    sys.exit()
            if animateFlow.testType == 2 and convalue_n[j][i] == 2:
                animateFlow.sCount+=1
                if animateFlow.sCount >1:
                    recordBranch()
                    animateFlow.running = 0
                    sys.exit()

        else:
            if convalue_ld[j][i]>1:
    ##	    #print 'ld'
                f_count=0
                l_count=0
                for p in range(1,NEIGHBOR_SIZE):
                    if i-p>0 and j-p>0:
                        f_count,former_depth1,start[0]=self.checkNextPixel(i-p,j-p,f_count,p,start[0],former_depth1,depthMAT,im)
    
                if f_count==0:
                    f_count=1
                f_mean1=former_depth1/f_count
    ##	    #print 'ld former: ',f_mean1
                for p in range(1,NEIGHBOR_SIZE):
                    if i+p<cols and j+p<rows:
                        l_count,latter_depth1,stop[0]=self.checkNextPixel(i+p,j+p,l_count,-p,stop[0],latter_depth1,depthMAT,im)
    
                if l_count==0:
                    l_count=1
                l_mean1=latter_depth1/l_count
    ##	    #print "ld latter: ",l_mean1
                neighbor_depth[0]= self.getMeanDepth(f_mean1,l_mean1,self.current_depth)-self.current_depth      
    				
    					 
            if convalue_rd[j][i]>1:
    ##	    #print 'rd'
                f_count=0
                l_count=0
                for p in range(1,NEIGHBOR_SIZE):
                    if i-p>0 and j+p<rows:
                        f_count,former_depth2,start[1]=self.checkNextPixel(i-p,j+p,f_count,p,start[1],former_depth2,depthMAT,im)
    
                if f_count==0:
                    f_count=1
                f_mean2=former_depth2/f_count
    ##	    #print 'rd former: ',f_mean2
                for p in range(1,NEIGHBOR_SIZE):
                    if i+p<cols and j-p>0:
                        l_count,latter_depth2,stop[1]=self.checkNextPixel(i+p,j-p,l_count,-p,stop[1],latter_depth2,depthMAT,im)
    
                if l_count==0:
                    l_count=1
                l_mean2=latter_depth2/l_count
                neighbor_depth[1]= self.getMeanDepth(f_mean2,l_mean2,self.current_depth)-self.current_depth
    
    				 
    					 
            if convalue_h[j][i]>1:
                f_count=0
                l_count=0
                for p in range(1,NEIGHBOR_SIZE): 
                    if i-p>0:
                        f_count,former_depth3,start[2]=self.checkNextPixel(i-p,j,f_count,p,start[2],former_depth3,depthMAT,im)
    
                if f_count==0:
                    f_count=1
                f_mean3=former_depth3/f_count
                #print 'h former: ',f_mean3
                for p in range(1,NEIGHBOR_SIZE):
                    if i+p<cols:
                        l_count,latter_depth3,stop[2]=self.checkNextPixel(i+p,j,l_count,-p,stop[2],latter_depth3,depthMAT,im)
    
    
                if l_count==0:
                    l_count=1
                l_mean3=latter_depth3/l_count
                
                neighbor_depth[2]= self.getMeanDepth(f_mean3,l_mean3,self.current_depth)-self.current_depth
    
            if convalue_v[j][i]>1:
                f_count=0
                l_count=0
                for p in range(1,NEIGHBOR_SIZE):
                    if j-p>0:
                        f_count,former_depth4,start[3]=self.checkNextPixel(i,j-p,f_count,p,start[3],former_depth4,depthMAT,im)
    
                if f_count==0:
                    f_count=1
                f_mean4=former_depth4/f_count
   
                for p in range(1,NEIGHBOR_SIZE):
                    if j+p<rows:
                        l_count,latter_depth4,stop[3]=self.checkNextPixel(i,j+p,l_count,-p,stop[3],latter_depth4,depthMAT,im)
    
                if l_count==0:
                    l_count=1
                l_mean4=latter_depth4/l_count
                neighbor_depth[3]= self.getMeanDepth(f_mean4,l_mean4,self.current_depth)-self.current_depth
                
                
            if self.hide == True:
                self.searchTrials-=1

                

            direction=np.argmin(neighbor_depth)
    
            index=0
            splitAr= []
            
            if convalue_n[j][i]>3 :
              
                if direction!=-1:
                    while index<4:
                        if abs(neighbor_depth[direction]-neighbor_depth[index])<=animateFlow.depth_range:                       
                            if index==0:
                                if im[j+1][i+1]==1:
                                    if self.checkFlag(i+1,j+1):
                                        b = (i+1,j+1)
                                        self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
        
        
                                if im[j-1][i-1]==1:
                                    if self.checkFlag(i-1,j-1):
                                        b = (i-1,j-1)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    
                            elif index==1:
                                if im[j-1][i+1]==1:
                                    if self.checkFlag(i+1,j-1):
                                        b = (i+1,j-1)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
                                if im[j+1][i-1]==1:
                                    if self.checkFlag(i-1,j+1): 
                                        b = (i-1,j+1)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    
                                
                            elif index==2:
                                if im[j][i+1]==1:
                                    if self.checkFlag(i+1,j): 
                                        b = (i+1,j)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    						
                                if im[j][i-1]==1:
                                    if self.checkFlag(i-1,j):                                  
                                        b = (i-1,j)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    
                                
                            elif index==3:
                                if im[j+1][i]==1:
                                    if self.checkFlag(i,j+1):
                                        b = (i,j+1)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    
                                if im[j-1][i]==1:
                                    if self.checkFlag(i,j-1):
                                        b = (i,j-1)
                                        if self.hide == False or self.searchTrials >= MAX_TRIALS-1:
                                            self.visit(b[0],b[1],self.newFlag(self.flag))
                                        splitAr.append(b)
    						#return nextPixel
    
                        index+=1
                        #print "branch",index
                #print "complete loop"  
                split_index=0
                Arlen=len(splitAr)
                #print '*************************Branches ',Arlen
                while split_index<Arlen:         
                    nextPixel=splitAr[split_index]
                    if split_index==0:
                        nextPixel0=copy.copy(nextPixel)
    			
                    else:
                        
                        self.handleIntersection(nextPixel,split_index,convalue_n)
                    split_index+=1


#
        if self.hide == True:
            self.last_depth=depthMAT[j][i]
            self.color=(0,0,0,0)
        else:
            self.last_depth=self.current_depth
            self.color=(180,180,120,255)

        
        self.updateDirection(nextPixel0[0]-self.x,nextPixel0[1]-self.y)

        return nextPixel0


    




class AgentGroup(pygame.sprite.Group):
    def __init__(self, groupId, depth, x, y):
        pygame.sprite.Group.__init__(self)
        self.startx=x
        self.starty=y
        self.Id=groupId
        self.Num=1
        self.frame=animateFlow.frame
        self.agentsIds=1
        self.depth = depth
        self.addAgents()
        
##        self.group=pygame.sprite.Group()
        
    def addAgents(self):
        flag=float(self.Id+math.exp(-1/self.Num))
#        flag = self.Id * 10 + self.Num
        agent = FlowAgent(self, self.agentsIds, self.startx, self.starty, 1, flag)
        self.Num+=1
        
    # Add the agent to the group
        self.add(agent)
        
        #print "add agent \nagent id: ",self.Num

        




class animateFlow(object):
    depthMAT=None
    im=None
    window_width=0
    window_height=0
    background_image=None
    con_N=None
    con_R=None
    con_L=None
    con_H=None
    con_V=None
    groupId=2
    groups=[]
    frame=0
    distance=[]
    width_ave=0
    depth_range=0
    backgroundMatrix=None
    color_depthMAT = None
    testType = 0
    sCount = 0
    running=1
    def __init__(self,im1,im2,depthMAT1,color_depthMAT,testType=0):

        
        animateFlow.testType = testType
        self.im2=im2.transpose()

        
        animateFlow.backgroundMatrix=self.im2
        animateFlow.im=np.copy(im1)
        FlowAgent.PathFlag=np.copy(im1).astype(float)
        animateFlow.depthMAT=np.copy(depthMAT1)
#        animateFlow.depth_range=depthMAT1[depthMAT1>0].mean()/LEVEL
        animateFlow.depth_range=np.median(depthMAT1[depthMAT1>0])/LEVEL

        animateFlow.window_width = int(animateFlow.im.shape[1])
        animateFlow.window_height = int(animateFlow.im.shape[0])


        pygame.init()
        animateFlow.screen = pygame.display.set_mode((animateFlow.window_width, animateFlow.window_height))
#        animateFlow.background_image = pygame.surfarray.make_surface(self.im2).convert()
        animateFlow.color_depthMAT = color_depthMAT
        animateFlow.background_image = self.colorVessels(self.im2,color_depthMAT)
        
        
        self.originalimage = animateFlow.background_image
      
        self.index = 0
        self.getConvolution()
        self.startAnimation()
        
        
        
    def colorVessels(self,binary_ves,color_depthMAT):
        ###########################################################################
        ## Colouring the vessels based on depth.
        ###########################################################################
        rows,cols = binary_ves.shape

        edge1 = roberts(binary_ves)
        edge2,edge3 = np.gradient(color_depthMAT)

        animateFlow.distance = ndimage.distance_transform_cdt(binary_ves , return_distances=True)
        animateFlow.distance=animateFlow.distance.transpose()

        animateFlow.width_ave=self.ave(animateFlow.distance)

        
        img = pygame.surfarray.make_surface(binary_ves).convert()
        for i in range(0,rows):
            for j in range(0,cols):
                if img.get_at((i,j))!=(0,0,0,255):
                    
                    if edge1[i][j]>0:
                        img.set_at((i,j),(120,120,120,180))
                    elif edge2[j][i] >= 1.2 * animateFlow.depth_range or edge3[j][i] >= 1.2 * animateFlow.depth_range:
                        img.set_at((i,j),(120,120,120,180))
                        
                    else:   
                        fill = 0
#      
                        i_c = -2
                        while i_c < 2 and fill == 0:
                            i_c += 1
                            j_c = -2
                            while j_c <2 and fill == 0:
                                j_c += 1
                                if 0 <= j+j_c < cols and 0 <= i+i_c < rows:
                                    if abs(color_depthMAT[j][i]-color_depthMAT[j+j_c][i+i_c]) < 1*animateFlow.depth_range and img.get_at((i,j))!=(0, 0, 85, 255):
                                        color = img.get_at((i,j))
                                        fill = 1
                                        break
                        if fill == 0:
                            if 0<color_depthMAT[j][i]<=40:
                                color = (255,0,0,180)
                            elif color_depthMAT[j][i]<=80:
                                color = (220,0,0,180)
                            elif color_depthMAT[j][i]<=120:
                                color = (200,0,0,180)
                            elif color_depthMAT[j][i]<=160:
                                color = (180,0,0,180)
                            elif color_depthMAT[j][i]<=200:
                                color = (150,0,0,180)
                            elif color_depthMAT[j][i]<=240:
                                color = (120,0,0,180)
                            else:
                                color = (100,0,0,180)
                            
         
                        img.set_at((i,j),color)
        
        return img


    def ave(self,dis_img):
        total=0
        count=0
        for pixel in np.nditer(dis_img):   
            if pixel>0:
                total+=pixel
                count+=1
        return total/count
    

    

            
#    @profile(immediate=True)
    def startAnimation(self):
        ###########################################################################
        ## Strating animation, receiving mouse click rto start the partical movement.
        ###########################################################################
        found=0
        clock = pygame.time.Clock()
        x=0
        y=0
        
        count_round=1
        
        
        while animateFlow.running:
            animateFlow.screen.blit(pygame.transform.scale(animateFlow.background_image,(animateFlow.window_width,animateFlow.window_height)), (0, 0))
            ev = pygame.event.get()

            for event in ev:
                if event.type==pygame.QUIT:
                    animateFlow.running=0
                    pygame.display.quit()
                    break

                elif event.type==pygame.MOUSEBUTTONUP:
                    x,y=pygame.mouse.get_pos()

                    found=1
                    if animateFlow.im[y][x]==0:
                        found=0
                        x,y,found=self.calibratePosition(found,x,y)
                        if found==1:
                            animateFlow.groups.append(AgentGroup(animateFlow.groupId, animateFlow.depthMAT[y][x],x,y))
                            animateFlow.groupId+=1
                        
#                            found=0
#            if count_round<10:
#                for i in range(0,40):
#                    found=0
#                    x,y,found=self.startMultiFlow(found)
#                    if found==1:
#                        animateFlow.groups.append(AgentGroup(animateFlow.groupId, animateFlow.depthMAT[y][x],x,y))
#                        animateFlow.groupId+=1
#                        found=0
            animateFlow.screen.blit(pygame.transform.scale(animateFlow.background_image,(animateFlow.window_width,animateFlow.window_height)), (0, 0))
            #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
            #print "frame: ",animateFlow.frame
            animateFlow.frame+=1
            self.updateFlow()

##            #image = pygame.image.load('..//images//cell.jpg').convert()
            msElapsed = clock.tick(30)
            #print "msElapsed: ",msElapsed
            pygame.display.flip()
            count_round+=1

        #print'Finish!'
##    #print animateFlow.im.shape,animateFlow.depthMAT.shape
        pygame.quit()
##        sys.exit()

            

    def startMultiFlow(self,found):
        ###########################################################################
        ## Automatic starting multi-flows when testing simple scenarios.
        ###########################################################################
        while found!=1:
            xi=random.randint(0,animateFlow.window_width-1)
            yi=random.randint(0,animateFlow.window_height-1)
            if animateFlow.im[yi][xi] > 0 and animateFlow.con_N[yi][xi]>=2:
                found=1
        return xi,yi,found
            
    def RD_Cov(self, im):
        k_rd=np.array([[0,0,1],[0,1,0],[1,0,0]])
        return ndimage.convolve(im,k_rd,mode='constant',cval=0.0)
    

    def LD_Cov(self, im):
        k_ld=np.array([[1,0,0],[0,1,0],[0,0,1]])
        return ndimage.convolve(im,k_ld,mode='constant',cval=0.0)

    def Ver_Cov(self, im):
        k_v=np.array([[0,1,0],[0,1,0],[0,1,0]])
        return ndimage.convolve(im,k_v,mode='constant',cval=0.0)

    def Hor_Cov(self, im):
        k_h=np.array([[0,0,0],[1,1,1],
                  [0,0,0]])
        return ndimage.convolve(im,k_h,mode='constant',cval=0.0)
    
    def Neigh_Cov(self, im):
        k_n=np.array([[1,1,1],[1,1,1],[1,1,1]])
        return ndimage.convolve(im,k_n,mode='constant',cval=0.0)

    def getConvolution(self):
        im0=np.copy(animateFlow.im)
        im1=np.copy(animateFlow.im)
        im2=np.copy(animateFlow.im)
        im3=np.copy(animateFlow.im)
        im4=np.copy(animateFlow.im)

        animateFlow.con_R=self.RD_Cov(im1)
        animateFlow.con_L=self.LD_Cov(im2)
        animateFlow.con_V=self.Ver_Cov(im3)
        animateFlow.con_H=self.Hor_Cov(im4)
        animateFlow.con_N=self.Neigh_Cov(im0)

    def updateFlow(self):

        if animateFlow.groups!=[]:
            for g in animateFlow.groups:

                g.update()

                g.draw(animateFlow.screen)

    def calibratePosition(self,found,x,y):
        region=0
        while found==0:
            bound=-region
            while bound<region:
                if animateFlow.im[y-region][x+bound]>0:
                    y=y-region
                    x=x+bound
                    found=1
                    break
                elif animateFlow.im[y+region][x+bound]>0:
                    y=y+region
                    x=x+bound
                    found=1
                    break
                elif animateFlow.im[y+bound][x-region]>0:
                    y=y+bound
                    x=x-region
                    found=1
                    break
                elif animateFlow.im[y+bound][x+region]>0:
                    y=y+bound
                    x=x+region
                    found=1
                    break
                bound+=1
            region+=1
        return x,y,found




    





