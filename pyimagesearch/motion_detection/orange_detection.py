import cv2
import numpy as np
import imutils

class OrangeCircleDetector:
    # def __init__(self):
        # You can set a fixed window for displaying results if needed
        # cv2.namedWindow("Results") # Removed this line

    def detect(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define the range for orange color in HSV
        lower_orange = np.array([5, 100, 100])  # Lower bound for orange (Hue, Saturation, Value)
        upper_orange = np.array([25, 255, 255]) # Upper bound for orange (Hue, Saturation, Value)

        mask = cv2.inRange(hsv, lower_orange, upper_orange)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Contours detection
        contours = cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        shapes = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 400:
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                x = approx.ravel()[0]
                y = approx.ravel()[1]

                shape_name = ""
                if len(approx) == 3:
                    shape_name = "Triangle"
                elif len(approx) == 4:
                    shape_name = "Rectangle"
                elif 10 < len(approx) < 20:
                    shape_name = "Circle"

                if shape_name:
                    shapes.append((approx, (x, y), shape_name))

        return mask, shapes

def draw_shapes(image, shapes):
    font = cv2.FONT_HERSHEY_COMPLEX
    for approx, (x, y), shape_name in shapes:
        cv2.drawContours(image, [approx], 0, (0, 0, 0), 5)
        cv2.putText(image, shape_name, (x, y), font, 1, (0, 0, 0))
