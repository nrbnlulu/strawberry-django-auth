CHANGELOG
=========

0.374.4 - 2023-05-07
--------------------

This is a dependencies update release.

If you use captcha validation you will need to

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #377](https://github.com/nrbnlulu/strawberry-django-auth/pull/377/)


0.374.3 - 2023-04-06
--------------------

Correctly pluralizes the "UserStatus" model as "User statuses" in Django Admin.

Without this change, Django Admin automatically uses the string "User statuses" as the verbose plural name.

Achieved by overriding the `Meta` (Django model subclass) attribute `verbose_name_plural`.

Contributed by [Justin Masayda](https://github.com/keysmusician) via [PR #368](https://github.com/nrbnlulu/strawberry-django-auth/pull/368/)


0.374.2 - 2023-03-25
--------------------

This release fixes release bot.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #355](https://github.com/nrbnlulu/strawberry-django-auth/pull/355/)


0.374.1 - 2023-03-24
--------------------

This release just updates dependencies.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #354](https://github.com/nrbnlulu/strawberry-django-auth/pull/354/)
