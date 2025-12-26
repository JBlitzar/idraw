import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

from pyaxidraw import axidraw

img = cv2.imread("portrait.jpg", cv2.IMREAD_GRAYSCALE)
WIDTH_PX = 200
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
img = cv2.equalizeHist(img)

edges = cv2.Canny(img, 250, 300)

cv2.imwrite("portrait_output.png", edges)