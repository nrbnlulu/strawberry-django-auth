from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

USERNAME = "1234567890"
PASSWORD = "1234567890"


class Command(BaseCommand):
    help = "Create a superuser automatically"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(phone_number=USERNAME).exists():
            user = User.objects.create_superuser(USERNAME, PASSWORD)
            status = user.status
            status.verified = True
            status.save(update_fields=["verified"])
            self.stdout.write(self.style.SUCCESS("Successfully created a new superuser"))
        else:
            self.stdout.write(self.style.WARNING("Superuser already exists."))
