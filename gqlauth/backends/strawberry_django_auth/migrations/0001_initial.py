# Generated by Django 4.1.7 on 2023-04-10 17:51

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Captcha",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("text", models.CharField(editable=False, max_length=50)),
                ("insert_time", models.DateTimeField(auto_now_add=True)),
                ("tries", models.IntegerField(default=0)),
                (
                    "image",
                    models.ImageField(
                        editable=False,
                        help_text="url for the captcha image",
                        upload_to="captcha/%Y/%m/%d/",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("token", models.CharField(editable=False, max_length=255, verbose_name="token")),
                ("created", models.DateTimeField(auto_now_add=True, verbose_name="created")),
                ("revoked", models.DateTimeField(blank=True, null=True, verbose_name="revoked")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_tokens",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "refresh token",
                "verbose_name_plural": "refresh tokens",
                "unique_together": {("token", "revoked")},
            },
        ),
    ]
