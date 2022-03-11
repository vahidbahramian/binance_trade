from django.shortcuts import render
from django.views.generic import View
import json
from requests import get
from django.http import *

# Create your views here.
import copy

from MainCode import main

a = main.Main()

class setData(View):

	def get(self, request):
		###### Write your code here if it is get method

		return True

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
