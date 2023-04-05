Release type: patch


Correctly pluralizes the "UserStatus" model as "User statuses" in Django Admin.

Without this change, Django Admin automatically uses the string "User statuss" as the verbose plural name.

Achieved by overriding the `Meta` (Django model subclass) attribute `verbose_name_plural`.
