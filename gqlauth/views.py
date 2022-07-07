from django.shortcuts import render


def activate(request):
    return render(request, "email/activation_email.html")
