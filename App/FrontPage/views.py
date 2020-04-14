import os
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.middleware.csrf import get_token
from django.http import JsonResponse

from io import BytesIO
import cv2
import numpy as np
import datetime
import base64
from PIL import Image
from io import BytesIO

def index(request):
	csrf_token = get_token(request)
	print(csrf_token)
	return render(request,'index.html')


def reccoord(request):
	print("RecCoord")
	if request.is_ajax():
		request_data = request.POST
		if int(request_data['check']) == 1:
			data = request_data['coordinates']
			data = data.split('===')[:-1]
			temp = []
			for item in data:
				t = item.split(',')
				temp.append([float(i) for i in t])
			coord = temp.copy()
			width = int(request_data['width'])
			height = int(request_data['height'])
			image_url = request_data['image']
			temp_header = image_url.split(',')[0]
			image_url  = image_url.split(',')[1]
			image_url = image_url.encode()

			fin_val = MarkContour(image_url,temp,width,height,1)
			fin_val = temp_header+','+str(fin_val)[1:][1:-1]
			return JsonResponse({'coord':coord,'image':fin_val})

		else:
			temp = []
			width = int(request_data['width'])
			height = int(request_data['height'])
			image_url = request_data['image']
			temp_header = image_url.split(',')[0]
			image_url  = image_url.split(',')[1]
			image_url = image_url.encode()

			fin_val = MarkContour(image_url,temp,width,height,0)
			return JsonResponse({'coord':fin_val})

	return render(request,'index.html')



def MarkContour(image_url,coord,width,height,chk):
	ts = datetime.datetime.now().timestamp()
	filename = "tempfiles/"+str(int(ts)) + "temp.jpg"

	with open(filename, "wb") as new_file:
		new_file.write(base64.decodebytes(image_url))

	image = cv2.imread(filename)
	print(width,height)
	image = cv2.resize(image, (width, height),interpolation = cv2.INTER_NEAREST)
	os.remove(filename)
	tempim = image.copy()
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blur = cv2.GaussianBlur(gray, (9,9), 0)

	if chk == 1:
		thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,85)
	else:
		thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

	# Dilate to combine adjacent text contours
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
	dilate = cv2.dilate(thresh, kernel, iterations=4)

	# Find contours, highlight text areas, and extract ROIs
	cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if len(cnts) == 2 else cnts[1]
	width, height = dilate.shape[:2]
	print(width,height)

	if chk == 1:
		for item in coord:
			x,y,w,h = int(item[0]),int(item[1]),int(item[3]),int(item[2])
			cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 1)
			contours = np.array( [ [x,y],[x,y+h],[x+w,y+h],[x+w,y] ] )
			dilate = dilate.copy()
			cv2.fillPoly(dilate, pts =[contours], color=(255,255,255))
	else:
		ini_coord = []
		ROI_number = 0
		for c in cnts:
			area = cv2.contourArea(c)
			if area > 500:
				x,y,w,h = cv2.boundingRect(c)
				xtemp = [x,y,w,h]
				ini_coord.append(xtemp)
		print(ini_coord)
		return ini_coord


	img = tempim.copy()
	dst = cv2.inpaint(img, dilate, 3, cv2.INPAINT_NS)

	ts = datetime.datetime.now().timestamp()
	filename = "tempfiles/"+str(int(ts)) + "temp.jpg"
	cv2.imwrite(filename, dst)

	with open(filename, "rb") as image_file:
		encoded_string = base64.b64encode(image_file.read())
	# os.remove(filename)
	return encoded_string





























