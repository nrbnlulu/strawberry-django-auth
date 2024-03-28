from django.shortcuts import render


def index(request):
    template = "index.html"  # Replace with your actual template name
    context = {}  # You can add context data if needed
    return render(request, template, context)
