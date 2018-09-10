import RPi.GPIO as GPIO
import cv2
import numpy as np
import time
import os

servos = []
servoPins = [23,24]
convCtrlPin = 18
emgBtn = 17
fwdBtn = 27
revBtn = 22
camera = None

def camSetup():
	os.system("sudo modprobe bcm2835-v4l2");
	delay(1);
	camera = cv2.VideoCapture(0)
	camera.set(3,640)
	camera.set(4,480)

def btnSetup():
	GPIO.setup(emgBtn, GPIO.IN)
	GPIO.setup(fwdBtn, GPIO.IN)
	GPIO.setup(revBtn, GPIO.IN)

def servoSetup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(servoPins[0],GPIO.OUT)
	GPIO.setup(servoPins[1],GPIO.OUT)
	GPIO.setup(convCtrlPin,GPIO.OUT)
	servos[0] = GPIO.PWM(servoPins[0],100)
	servos[1] = GPIO.PWM(servoPins[1],100)
	servos[0].start(100)
	servos[1].start(100)

def convStart():
	GPIO.output(convCtrlPin,GPIO.HIGH)

def convDrive(dir):
	if dir:
		servos[0].ChangeDutyCycle(20)
	else:
		servos[0].ChangeDutyCycle(10)

def convStop():
	GPIO.output(convCtrlPin,GPIO.LOW)

def convSwitch(lane):
	if lane:
		servos[1].ChangeDutyCycle(20)
	else:
		servos[1].ChangeDutyCycle(13)

def delay(sec):
	time.sleep(sec)

def killCamera():
	camera.release()
	cv2.destroyAllWindows()

if __name__ == "__main__":
	btnSetup()
	servoSetup()
	camSetup()
	convSwitch(1)
	while True:
		while GPIO.input(emgBtn):
			if GPIO.input(fwdBtn):
				convStart()
				convDrive(1)
			elif GPIO.input(revBtn):
				convStart()
				convDrive(0)
			else:
				convStop()
		convStart()
		convDrive(1)
		ret,img = camera.read()
		if ret:
			im = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
			maskGreen = cv2.inRange(im,np.array(( 30, 50, 30), dtype=np.uint8, ndmin=1),np.array(( 80, 255, 255), dtype=np.uint8, ndmin=1))
			maskRed1= cv2.inRange(im,np.array(( 0, 60, 50), dtype=np.uint8, ndmin=1),np.array(( 10, 255, 255), dtype=np.uint8, ndmin=1))
			maskRed2= cv2.inRange(im,np.array(( 170, 60, 5), dtype=np.uint8, ndmin=1),np.array(( 180, 255, 255), dtype=np.uint8, ndmin=1))
			maskRed = maskRed1 | maskRed2				
			maskGreen, greenContours, hierarchy = cv2.findContours(maskGreen, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
			maskRed, redContours, hierarchy = cv2.findContours(maskRed, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
			gFlag, rFlag = False, False
			for cnt in greenContours:
				if cv2.contourArea(cnt) >= 3000:
					gFlag = True
					cv2.drawContours(img, [cnt], 0, (0,255,0), 1)
					ellipse = cv2.fitEllipse(cnt)
					(x,y),radius = cv2.minEnclosingCircle(cnt)
    					center = (int(x),int(y))
   					radius = int(radius)
					cv2.circle(img,center,radius,(0,255,0),2)
					cv2.ellipse(img,ellipse,(0,255,0),2)
			for cnt in redContours:
				if cv2.contourArea(cnt) >=3000:
					rFlag = True
					cv2.drawContours(img, [cnt], 0, (0,0,255), 1)
					ellipse = cv2.fitEllipse(cnt)
					(x,y),radius = cv2.minEnclosingCircle(cnt)
    					center = (int(x),int(y))
   					radius = int(radius)
					cv2.circle(img,center,radius,(0,0,255),2)
					cv2.ellipse(img,ellipse,(0,0,255),2)
			cv2.imshow("IMG",img)
			print(bFlag,gFlag,rFlag)
			if gFlag and not rFlag:
				print("Lane Right")
				convSwitch(1)
			elif rFlag and not gFlag:
				print("Lane Left")
				convSwitch(0)
			elif gFlag and rFlag: 
				print("Lane Mid")
				convStop()
			else:
				print("Do nothing")
			key = cv2.waitKey(1)
			if key == ord('q'):
				killCamera()
				break
		else:
			print("Error: No camera frame captured")
