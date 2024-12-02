from django.db import models


class Apple(models.Model):
    class Meta:
        permissions = [("can_eat", "can eat apples")]

    color = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_eaten = models.BooleanField(default=False)
