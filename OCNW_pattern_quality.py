
__doc__ = """
    OCNW embossing pattern quality assessment tool.
    Usage:
        Run this code in the folder, all image files with suffix of ".CR2" and ".JPG" will be assessed.
        An "results.csv" file is dumpped when finished.
    Or:
        Run this code with an image file name as input, datum will be printed.

    Please report bugs to <zhao.l.3@pg.com>.
"""
__version__ = '20240809'

import os, sys

try:
    from PIL import Image
except:
    raise Exception("Please install PIL")
import base64
import io
try:
    from skimage.color import rgb2gray
except:
    raise Exception("Please install scikit-image")
try:
    import numpy as np
except:
    raise Exception("Please install numpy")
from skimage.morphology import label
from skimage.measure import regionprops
from skimage.feature import match_template
from scipy.ndimage import maximum_filter
try:
    import cv2
except:
    raise Exception("Please install python-opencv")
try:
    import pandas as pd
except:
    raise Exception("Please install pandas")
from time import time

ColorCardWidth = 1091

def locate_color_card(img, name):
    """
    img: gray scale from 0 to 1
    """
    tot_area = img.shape[0] * img.shape[1]
    y, x = np.histogram(img.ravel(), bins=100)
    x = x[:-1] + (x[1]-x[0])*0.5
    x_low = (x.max() - x.min())*0.2
    mask = img < x_low

    ## omit top and bottom part to reduce complexity:
    mask[:int(img.shape[0]*0.1), :] = False
    mask[int(img.shape[0]*0.9):, :] = False

    labeled = label(mask)
    props = regionprops(labeled)
    isNotFound = True
    for p in props:
        ## check if a right size:
        if p.area_convex < tot_area*0.072 or p.area_convex > tot_area*0.085: continue
        else:
            ## check if a square:
            if 1.60 < (p.bbox[2]-p.bbox[0])/(p.bbox[3]-p.bbox[1]) <= 1.70:
                isNotFound = False
                break
    if isNotFound:
        err = "Color card not located:"+name
        return None, None

    color_card_width = np.sqrt(p.area_convex*0.6)
    return p.centroid, color_card_width


def get_focus_area(img_scaled, color_card_centroid):
    half_width = img_scaled.shape[1]*0.5
    h0 = int(img_scaled.shape[0]*0.1)
    h1 = int(img_scaled.shape[0]-h0)
    if color_card_centroid[1] > half_width:
        w0 = int(img_scaled.shape[1]*0.05)
        w1 = int(color_card_centroid[1] - ColorCardWidth*0.5 - w0)
    else:
        w0 = int(color_card_centroid[1]+ColorCardWidth*0.5 + img_scaled.shape[0]*0.05)
        w1 = int(img_scaled.shape[1]*0.95)
    focus_area = img_scaled[h0:h1, w0:w1]
    return focus_area

def get_template(): 
    string = ["iVBORw0KGgoAAAANSUhEUgAAAVUAAACrAQAAAAD+mDJeAAAD8k",
          "lEQVR4nO1YO47bMBB9EoNVCgNKuUUA5Qgu08lH2WOkk8qUewQf",
          "RWVKH0FFii2VIIV3Ye+koPidGVpdgMBT7Nri8/DNmyE5InC3u9",
          "3tXxkRXbSxOv3aAzDnTV4bIiKiaQu2t1iVRWSGaLPjzmE3MCZv",
          "4y1oE7DzLWwfsLeiq4g2k2hi7CIAorx9jZ/vpInDR9IGuF+TDs",
          "wlbDbrYwm7TwceONZbotgN1Zxilw2p67w3c7N+huCsJSKidx0b",
          "jw9lwibm2JQJ23mTSRhhp+8eAF7d009AQeF0mVUlwiaLvC+s0D",
          "ar2fx7zHcPAM/h8W9AruGVbiL+oGajYhq1anAN096o2ejiRARW",
          "S/rIxvYE4JoOHKAsUMFJw6eq/Z9TOvAGABP323IflvDM/e45XU",
          "tYWMziptSybNRYt5hTjv0DoBpz7AMghHF1RBLr5Nz3ObMaNhNv",
          "HDtDyIaSepaNet0gjxwrZYOLE80XE67tohWxBwAfU+wTrJjMTs",
          "gXfqUu2YatDSMVTvAyx09aUo++IV+Fvb7XZkurxgHAi4xdgETh",
          "inQOJlO4ITU2m43gp7ZizzL2gPiMrPcAxMXiXXg/9cEykbEvsZ",
          "9H17dMIraK98RvDrvIjofIz9lhldOsC36MxyqHQxP8NAE764Qt",
          "iS5glZIY/NgQsErqOj9G5xpYkziJWFtVs00f0dwWVLOEL0BD5x",
          "o4/gKgnVBWHzPhEQBRTEojfMFAZ9DFNQQy4bW3WYjOoAWrMiXC",
          "VjmasR4ChQXqsCMcCRnbBux7+LFM2ATsJUQrE46qYAnRKoQ7h6",
          "0t9hVgnaozv3nUR/v/AGgl4TomX4ltgXBvOUyu5yo1LT/svzDr",
          "oCuc9I/AGu0oY7tMJd7GBMv3QN4eZSSm0K/TCLWFNEAqaIFwS9",
          "lmUyDc5wVQILyGFt4vaATwQaV7St6djlDKZwfktdJo9d7nockd",
          "nad7RsKBRqTnekw3PwE7PhewlmvOjZ/rni6rQLk7UA7WQQqukU",
          "PupMx1spSNFJyyYIwQXPSWktxrSC3kDhC7Qt5CrhRmAdsyefS3",
          "KN5TtdFyT+9h3oGs+vYaXZ4NS0Gia4WPCbcqXd7zDtnuFFv2ym",
          "QoXrDZHdMViBulzwDUTi/Lvt14FaitKkfCRqbeySSHjHW7uLGM",
          "rz3CzGjd2kcnzS8iV1Sm6w6S0X8q3UN0tMo/rG5nP8Q2OytmFW",
          "Y++k/syqfKMnoN3nIdkBeK+OaREvYW/ZRfOzVJ4BEFziFbBDEF",
          "jqVD/O1ZJwtEDU5eN9xvMu3PstuoyyrVwmpBtdt3mr7Lun2lGU",
          "hsuYN1SkwbsJXMVtAMoC8AgO8b3MI1Itus2iDt3e7239pf3mE8Z9e6UzkAAAAASUVORK5CYII="]
    string = ''.join(string)
    decoded_data = base64.b64decode(string)
    image = Image.open(io.BytesIO(decoded_data))
    image = np.array(image)
    # image = binary_dilation(image)
    image = image[15:image.shape[0]-15, :]
    return image

def match_pattern(img, template):
    """
    img: grayscale [0, 1]
    """
    matching = match_template(img, template, pad_input=True)
    peaks = maximum_filter(matching, size=100)
    mask = (matching==peaks)
    coords = np.where(mask)
    xys = list(zip(coords[0], coords[1]))
    heights = [peaks[a] for a in xys]
    ndx_max_to_min = sorted(range(len(heights)), key=lambda k: heights[k], reverse=True)
    return peaks, heights, ndx_max_to_min

def calt_one_image(fname):
    img = np.array(Image.open(fname))
    img_gray = rgb2gray(img)

    color_card_loc, color_card_width = locate_color_card(img_gray, fname)
    if color_card_loc is None:
        print('Color card location error for sample:', fname)
        return None

    ratio = ColorCardWidth/color_card_width
    color_card_loc = [a*ratio for a in color_card_loc]
    img_gray = cv2.resize(img_gray, None, fx=ratio, fy=ratio)
    focus_area = get_focus_area(img_gray, color_card_loc)

    template = get_template()
    area = (focus_area.shape[0]-template.shape[0]*1)*(focus_area.shape[1]-template.shape[1]*1)
    area_temp = template.shape[0]*template.shape[1]
    n_match = int(area/area_temp)

    pat = template[:, :]
    _, heights0, _ = match_pattern(focus_area, pat)
    heights0.sort(reverse=True)
    heights0 = heights0[:n_match]

    pat = template[::-1, :]
    _, heights1, _ = match_pattern(focus_area, pat)
    heights1.sort(reverse=True)
    heights1 = heights1[:n_match]

    if sum(heights0)>sum(heights1): return heights0
    else: return heights1


if __name__=='__main__':
    print(__doc__)
    if '-h' in sys.argv or '--help' in sys.argv: sys.exit()

    if len(sys.argv)==2 and os.path.isfile(sys.argv[1]):
        hist = calt_one_image(sys.argv[1])
        res = sum(hist)/len(hist)
        print(res)
        sys.exit()

    res = {}
    i = 0 
    for p, ds, fs in os.walk('.'):
        for name in fs:
            suffix = name[-4:].upper()
            if suffix == '.JPG' or suffix == '.CR2':
                t = time()
                fname = p + '/' + name
                hist = calt_one_image(fname)
                if hist is None: continue
                res[fname] = sum(hist)/len(hist)
                print(fname, time()-t)
                i += 1

    jpg = [{'file_name':a, 'value':b} for a, b in res.items()]
    pd.DataFrame(jpg).to_csv('results.csv')
    print('\nDone.')
    sys.exit()

    jpg = [{'file_name':a, 'value':b} for a, b in res.items() if a.endswith('.JPG')]
    cr2 = [{'file_name':a, 'value':b} for a, b in res.items() if a.endswith('.CR2')]

    pd.DataFrame(jpg).to_csv('jpg_data.csv')
    pd.DataFrame(cr2).to_csv('cr2_data.csv')
