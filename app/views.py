from django.shortcuts import render
from django.views.generic import View
import json
from requests import get
from django.http import *

# Create your views here.
import copy

from MainCode import main


class setData(View):
	global a
	##if not a:
	a = main.Main()
	def get(self, request):
		###### Write your code here if it is get method

		response = {'Result': True}
		response = json.dumps(response)
		return HttpResponse(response, content_type='application.json')

	def post(self, request):
		try:

			###### Write your code here if it is post method



			response = {'Result': True}
			response = json.dumps(response)
			return HttpResponse(response, content_type='application.json')
		except Exception as e:
			response = {'Result': str(e)}
			response = json.dumps(response)
			return HttpResponse(response, content_type='application.json')
