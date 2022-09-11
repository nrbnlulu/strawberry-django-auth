from django.contrib import admin
from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()

admin.site.register(USER_MODEL)
