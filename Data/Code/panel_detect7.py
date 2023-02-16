import cv2 as cv
import numpy as np
from cmath import inf
import math

import time

#start = time.time()
#print("hello")

#open video reading object
cap = cv.VideoCapture('IMG_5312.MOV')

#cheach video input dims
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

#build output object
out = cv.VideoWriter('outpy.avi',cv.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))

if (cap.isOpened()== False): 
    print("Error opening video stream or file")

#for debugging
frame_count = 0

# Read until video is completed
while(cap.isOpened()):
# Capture frame-by-frame
    ret, input = cap.read()
    if ret == True:

        #convert to gray scale:
        gray = cv.cvtColor(input, cv.COLOR_BGR2GRAY)

        #apply a blur:
        blurred = cv.medianBlur(gray,7)
        #blurred = cv.GaussianBlur(gray,(3,3),0)
        painted = blurred.copy()

        #threshold the image to binary for contour func:
        #thr_val, threshed = cv.threshold(blurred, 60, 255, cv.THRESH_BINARY)
        thr_val, threshed = cv.threshold(blurred, 100, 255, cv.THRESH_BINARY)

        #get contours:
        #contour, heirachy = cv.findContours(threshed, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE) #this works
        contour, heirarchy = cv.findContours(threshed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) #testing this 

        #apply contour logic to remove small error detects
        contour_keeps = []      
        for cnt in contour:
            area = cv.contourArea(cnt)
            if area > 50000:
                contour_keeps.append(cnt)

        #debuging: shows all contours that will be measured
        showContour = cv.drawContours(input, contour_keeps, -1, (255, 0, 255), 2)  

        #initialize main meaurement lists
        measurements = []
        midpoints = []
        line_thick = []
        nominal = 22        #this needs to be a variable based on both the nominal gap value for the vehicle and should be influenced by the distance from the car
        nominal_bound = 4   #used to define upper and lower maximums of measurment that satisfy manufacturer standards, outside of this range will begin color change

        c = 0        #for color switching
        r_test = 15  #magnitude for unit vector

        Text = False #set this to true to see printed values of measurements (for debugging)
        
        colors = [(255, 0, 255), (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 0, 255), (0, 255, 0), (255, 0, 0), (0, 0, 255)]

        ################################
        ###     Main measure Loop   ####
        ################################
        for cnt in contour_keeps:

            color = colors[c]
            #reset values each iter:
            i = 0
            label_counter = 0
            measurements.clear()
            midpoints.clear()
            line_thick.clear()

            while True:

                #ensure points exist
                if i < (len(cnt) - 5):

                    #neighbor contour points on linearized curve
                    x1, y1 = cnt[i][0][0], cnt[i][0][1]
                    x2, y2 = cnt[i+5][0][0], cnt[i+5][0][1]
                    label_counter += 1

                #Calculate normal direction form contour            #this last bit may cause issues for flat sections
                if x1 != 0 and y1 != 0 and x1 != 0 and x2 != 0 and (0 < np.sqrt((x2-x1)**2 + (y2-y1)**2) < 150): #neccessary conditions to avoid jumping out of feasible range

                    if np.sqrt((x2 - x1)**2 + (y2 - y1)**2) < 100:
                        f = 0 #placeholder
                        #painted = cv.line(input, (x1, y1), (x2,  y2), color, 2)

                    #calculate midpoint between those contour points
                    x_midPoint, y_midPoint = int((x1 + x2)/2), int((y1 + y2)/2)
            
                    #vector from midpoint to 2nd point:
                    u = x2 - x_midPoint
                    v = y2 - y_midPoint

                    #normalize to unit vector
                    magnitude = np.sqrt(u**2 + v**2)
                    if math.isnan(magnitude) == False:
                        u = u/magnitude
                        v = v/magnitude
            
                    #rotate 90 degree to get ortho unit vector:
                    u_norm = -v
                    v_norm = u
            
                    #measurement section:
                    r = 5   #reset beggining radius for checking pixel value

                    while True:

                        #check to make sure no ill conditioned values
                        if (math.isnan(x_midPoint + r*u_norm) == False) and (math.isnan(y_midPoint + r*v_norm) == False):
                            x_endPoint, y_endPoint = int(x_midPoint + r*u_norm), int((y_midPoint + r*v_norm))

                            #make sure points are within image bounds
                            if (0 <= x_endPoint < input.shape[1]) and (0 <= y_endPoint < input.shape[0]):
                                 #check if new pixel is not a black pixel in the threshed image
                                if threshed[y_endPoint, x_endPoint] != 0:
                        
                                    #calculate euclidian distance to next contour
                                    dist = np.sqrt((r*u_norm)**2 + (r*v_norm)**2)
                                    dist = np.round(dist, 1) #round to first decimal
                                    measurements.append(dist)

                                    #midpoint of new measurement vector, will ber used for color mapping
                                    x_measuredMidpoint, y_measuredMidpoint = int(x_midPoint + (r*u_norm)/2), int(y_midPoint + (r*v_norm)/2)
                                    midpoints.append((x_measuredMidpoint, y_measuredMidpoint))

                                    #only put text every 5 measurements to reduce clutter, only for debugging
                                    if label_counter > 5 and Text == True:
                                        #painted = cv.putText(input, str(dist), (x_midPoint, y_midPoint), font, 1, (255, 0, 130), 2)
                                        label_counter = 0
                                    break  

                        #if no contour is found within 100 units, break and move on (probably not a panel gap at this distance)
                        if r > 100:
                            break

                        r += 1 

                if i < (len(cnt) - 2):
                    i += 2 #skip distance, dont want to compute this program at every single line point 
                else:
                    break
            c += 1 #next color in list
    
            #skipping last measurements to avoid bug issues
            for j in range(2, len(measurements)-1):
        
                #define an integer for painting the panel gap with proper thickness to fill
                line_thickness = int(measurements[j])

                #define a tone curve
                color_shift = int((1/nominal_bound) * (2*(measurements[j] - nominal))**2) #quadratic fit (shifted measurments so minima is at zero)

                #if exceeding RGB bound, restrict to (0, 255)
                if color_shift > 255:
                    color_shift = 255

                #if small gap, shift towards blue
                if (measurements[j] - nominal) < -nominal_bound:    color = (color_shift, 255 - color_shift, 0)
                #if gap large, shift towards red
                elif (measurements[j] - nominal) > nominal_bound:   color = (0, 255 - color_shift, color_shift)
                #otherwise gap is good, paint green
                else: color = (0, 255, 0)


                #print((midpoints[j][0] - midpoints[j-1][0])**2, (midpoints[j][1] - midpoints[j-1][1])**2)

                #make sure we don't paint random stray lines
                if (np.sqrt((midpoints[j][0] - midpoints[j-1][0])**2 + (midpoints[j][1] - midpoints[j-1][1])**2)) < 100:
           
                    #paints a line from current midpoint to previous midpoint on measured vectors
                    painted = cv.line(input, midpoints[j], midpoints[j-1], color, line_thickness)  #paints midpoint line

        out.write(painted)
        #for debugging, specify section of the input video to break at:
        #frame_count +=1
        #if frame_count > 400:
        #    break

    # Break the main loop
    else: 
        break

# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv.destroyAllWindows()
