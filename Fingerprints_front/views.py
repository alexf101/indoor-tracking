# Create your views here.
import logging
from django.shortcuts import render_to_response

log = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def home(request):
    return render_to_response('home.html')


def not_found(request, url):
    msg = "URL not found: "+url
    return render_to_response('home.html', {'msg': msg})


def how_to_use_api(request):
    return render_to_response('how_to_use_api.html')


def client_libs(request):
    return render_to_response('client_libs.html')


def contact(request):
    return render_to_response('contact.html')


def applications(request):
    return render_to_response('applications.html')