# -*- coding: utf-8 -*- 

###########################################################################
## This file is for the simple GUI for the software
###########################################################################

from Tkinter import *
from tkFileDialog import askopenfilename
from ttk import Frame, Button, Style

import numpy as np
# from PIL import Image
from animate_agent import animateFlow
from buildBG import reconstructVessels
from layer import connectSkeleton
from loadDepth import load_Depth
from segmentImage import segment_Image
from showImage import load_Image
from skeletonizeImage import skeletonize_Image
# from skimage import img_as_ubyte


###########################################################################
## Class Blood Vessel Simulation
###########################################################################

class Blood_Vessel_Simulation(Frame):
    def __init__( self, parent):
        Frame.__init__ ( self, parent)
        self.parent=parent;
        self.InitUI()
        

    def InitUI(self):
        global animation
        global skeleton_im
        global segmented_im
        global ref
        global depthMAT
        animation=None
        skeleton_im=None
        segmented_im=None
        ref=None
        depthMAT=None
        self.style=Style()
        self.style.theme_use("default")
        
        
        frame=Frame(self, relief=RAISED, borderwidth=1)
        frame.pack(fill=BOTH, expand=True)
        
        self.centerWindow()

        self.pack(fill=BOTH, expand=True)
        
###########################################################################
## Binding function to buttons
###########################################################################   
        
        
        self.load_Image = Button( self, text="Load Image", command=self.load_ImageOnclicked)
        self.load_Image.pack(side=LEFT)
        
        self.segment_Image = Button( self, text="Segment Image", command=self.segment_ImageOnclicked)
        self.segment_Image.pack(side=LEFT)
        
        self.skeleton_Image = Button( self, text="Skeletonize Image", command=self.skeletonize_ImageOnclicked)
        self.skeleton_Image.pack(side=LEFT)

        
        self.skeleton_Image = Button( self, text="get distance Image", command=self.distance_ImageOnclicked)
        self.skeleton_Image.pack(side=LEFT)
        
        self.animate = Button( self, text="Animate", command= self.animateOnclicked)
        self.animate.pack(side=LEFT)
        

        

    def centerWindow(self):
      
        w = 600
        h = 500

        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
        
        x = (sw - w)/2
        y = (sh - h)/2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
    
    
###########################################################################
## Presenting results in different stages.
###########################################################################

    def load_ImageOnclicked(self):
        ###########################################################################
        ## Displaying input image.
        ###########################################################################
        global initial_im
        global ref
        global initial_depth
        

        ImageName = askopenfilename(initialdir="F:\UWA\GENG5511\simulation\images",title = "Choose an image file.")
        
    #Using try in case user types in unknown file or closes without choosing a file.
        try:
            with open(ImageName,'r') as UseFile:
                print (ImageName)
        except:
            print("No file exists")
            
        DepthName = askopenfilename(initialdir="F:\UWA\GENG5511\simulation\images")
        
    #Using try in case user types in unknown file or closes without choosing a file.
        try:
            with open(DepthName,'r') as UseFile:
                print (DepthName)
        except:
            
            print("No file exists")
        ref,initial_im=load_Image(ImageName)
        initial_depth=load_Depth(DepthName,ref,initial_im)

    
    def segment_ImageOnclicked(self):
        ###########################################################################
        ## Displaying segemented image.
        ###########################################################################
        global initial_im
        global segmented_im
        global initial_depth
        global ref
        
        if initial_im is None:
            ref,initial_im=load_Image('..//images//mip.rmf')
            initial_depth=load_Depth('..//images//depth.rmf',ref,initial_im)
        segmented_im,initial_depth=segment_Image(initial_im,initial_depth)
        x=img_as_ubyte(segmented_im)
        
        Image.fromarray(x).show()
    
    def skeletonize_ImageOnclicked( self):
        ###########################################################################
        ## Displaying skeletonised image.
        ###########################################################################
        global segmented_im
        global skeleton_im
        global initial_depth
        global ref,depthMAT,im,convalue_n

        if segmented_im is None:

            ref,initial_im=load_Image('..//images//mip.rmf')
            initial_depth=load_Depth('..//images//depth.rmf',ref,initial_im)
            segmented_im,initial_depth=segment_Image(initial_im,initial_depth)
        skeleton_im=skeletonize_Image(segmented_im)
#        Image.fromarray(skeleton_im).show('initial')
#        im = Image.fromarray(skeleton_im)
#        im.save('../images/skeleton.bmp')
        upperrange=5
        im= np.copy(skeleton_im)
        depthMAT = np.copy(initial_depth)
        for ite in range(1,upperrange):
            if ite<upperrange-2:
                im,depthMAT,initial_depth,convalue_n=connectSkeleton(im,refPt,initial_depth,depthMAT)
            else:
                im,depthMAT,initial_depth,convalue_n=connectSkeleton(im,refPt,initial_depth,depthMAT,ComplexSmooth=True)
                
        print 'finish skeletonize!' 

    
    def animateOnclicked( self):
        ###########################################################################
        ## Final animation.
        ###########################################################################
        global refPt
        global skeleton_im
        global distance_im
        global animation
        global initial_depth
        global segmented_im,depthMAT,im,convalue_n
        
        

        if skeleton_im is None:
            self.load_ImageOnclicked()
            segmented_im,initial_depth=segment_Image(initial_im,initial_depth)
            skeleton_im=skeletonize_Image(segmented_im)
            
            upperrange=6
            im= np.copy(skeleton_im)
            depthMAT = np.copy(initial_depth)
            for ite in range(1,upperrange):
                if ite<upperrange-3:
                    im,depthMAT,initial_depth,convalue_n=connectSkeleton(im,refPt,initial_depth,depthMAT)
                else:
                    im,depthMAT,initial_depth,convalue_n=connectSkeleton(im,refPt,initial_depth,depthMAT,ComplexSmooth=True)
            print 'finish skeletonize!'
            
        dilated_im,initial_depth=reconstructVessels(segmented_im,depthMAT,im,convalue_n)
        print 'finish reconst'

        initial_depth = initial_depth * dilated_im

        
        self.animation=animateFlow(im,dilated_im,depthMAT,initial_depth)

        return


if __name__ == '__main__':
    global initial_im
    global segmented_im
    global refPt
    initial_im=None
    segmented_im=None
    refPt=None
    root = Tk()
    root.title("Blood Vessel Simulation")
    Blood_Vessel_Simulation(root)
    root.mainloop()
    print "quit the software"
   
    
    

