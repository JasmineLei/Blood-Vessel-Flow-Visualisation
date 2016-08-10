import pygame
import numpy as np
from PIL import Image
import random
import cv2
import SimpleITK as sitk
import matplotlib.pyplot as plt
from scipy.misc import imresize
from scipy import ndimage
from scipy.io import savemat
import time
from skimage import img_as_ubyte


im=np.array(Image.open('..//images//skeleton.png').convert('L'))
