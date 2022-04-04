from django.shortcuts import render
from django.http import HttpResponse
from . import models

def activate(request):
    return render(request, 'email/activation_email.html') 