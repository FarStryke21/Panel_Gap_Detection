import cv2 as cv


cap = cv.VideoCapture('IMG_5312.MOV')
#cap = cv.VideoCapture('outpy.avi')

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
#out = cv.VideoWriter('outpy.avi',cv.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))


if (cap.isOpened()== False): 
    print("Error opening video stream or file")

# Read until video is completed
while(cap.isOpened()):
# Capture frame-by-frame
    ret, input = cap.read()
    if ret == True:


        gray = cv.cvtColor(input, cv.COLOR_BGR2GRAY)

        #apply a blur:
        blurred = cv.medianBlur(gray,7)
        painted = blurred.copy()

        #threshold the image to binary for contour func:
        thr_val, threshed = cv.threshold(blurred, 100, 255, cv.THRESH_BINARY)
        #threshed = cv.adaptiveThreshold(blurred,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,  cv.THRESH_BINARY,11,2)

        #get contours:
        #contour, heirachy = cv.findContours(threshed, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE) #this works
        contour, heirarchy = cv.findContours(threshed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) #testing this 
        contour_keeps = []
        for cnt in contour:
            area = cv.contourArea(cnt)
            if area > 50000:
                contour_keeps.append(cnt)

        showContour = cv.drawContours(input, contour_keeps, -1, (255, 0, 255), 2)   

        # Display the resulting frame
        cv.imshow('Frame',showContour)
        cv.waitKey(5)

        #out.write(frame)

    # Press Q on keyboard to  exit
    #if cv.waitKey(25) & 0xFF == ord('q'):
        #break

    # Break the loop
    else: 
        break

# When everything done, release the video capture object
cap.release()

# Closes all the frames
cv.destroyAllWindows()