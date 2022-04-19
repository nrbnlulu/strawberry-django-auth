"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 3.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import sys
sys.path.append('/home/nir/Desktop/git clones/django/strawberry-django-auth/testproject')
BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = "FAKE_KEY"

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1']

ROOT_URLCONF = 'testproject.urls'

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'strawberry_django',
    'strawberry_django_jwt.refresh_token',
    'gqlauth',
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"


# custom settings start here


AUTHENTICATION_BACKENDS = [
    "gqlauth.backends.GraphQLAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_ALLOW_ANY_CLASSES": [
        "gqlauth.mutations.Register",
        "gqlauth.mutations.VerifyAccount",
        "gqlauth.mutations.ResendActivationEmail",
        "gqlauth.mutations.SendPasswordResetEmail",
        "gqlauth.mutations.PasswordReset",
        "gqlauth.mutations.ObtainJSONWebToken",
        "gqlauth.mutations.VerifyToken",
        "gqlauth.mutations.RefreshToken",
        "gqlauth.mutations.RevokeToken",
        "gqlauth.mutations.VerifySecondaryEmail",
    ],
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

GQL_AUTH = {
    "EMAIL_ASYNC_TASK": "testproject.pseudo_async_email_support.pseudo_async_email_support"
}