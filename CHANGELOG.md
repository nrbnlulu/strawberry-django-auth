CHANGELOG
=========
0.378.3 - 2024-12-02
--------------------
Release to PyPI for #586
See https://github.com/nrbnlulu/strawberry-django-auth/releases/tag/0.378.0

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #592](https://github.com/nrbnlulu/strawberry-django-auth/pull/592/)

0.378.2 - 2024-12-02
--------------------
Release to PyPI for #586
See https://github.com/nrbnlulu/strawberry-django-auth/releases/tag/0.378.0

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #591](https://github.com/nrbnlulu/strawberry-django-auth/pull/591/)

0.378.1 - 2024-12-02
--------------------
Release for #586

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #590](https://github.com/nrbnlulu/strawberry-django-auth/pull/590/)

0.378.0 - 2024-12-02
--------------------
- Add support for django 5.1
- Drop support for django 3.2 and python >=3.9
- Migrate from poetry to uv
- use taskfile instead of Makefile

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #589](https://github.com/nrbnlulu/strawberry-django-auth/pull/589/)

0.378.0 - 2024-12-02
--------------------
- Add support for django 5.1
- Drop support for django 3.2 and python >=3.9
- Migrate from poetry to uv
- use taskfile instead of Makefile

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #588](https://github.com/nrbnlulu/strawberry-django-auth/pull/588/)

0.377.0 - 2024-07-24
--------------------
resolve [#567](https://github.com/nrbnlulu/strawberry-django-auth/issues/567)resolve [#564](https://github.com/nrbnlulu/strawberry-django-auth/issues/564)Add support for CI mode when using captcha on login.this should enable to automate the sign-in process by not validation the captcha fields.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #569](https://github.com/nrbnlulu/strawberry-django-auth/pull/569/)

0.376.11 - 2024-04-10
--------------------
Fix register fails on channels requests. #137Do not call get_current_site() from get_email_context()Extract values from channels context.

Contributed by [Hyun S. Moon](https://github.com/shmoon-kr) via [PR #519](https://github.com/nrbnlulu/strawberry-django-auth/pull/519/)

0.376.10 - 2024-04-06
--------------------
try release 2

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #517](https://github.com/nrbnlulu/strawberry-django-auth/pull/517/)

0.376.9 - 2024-04-06
--------------------
try release 1

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #516](https://github.com/nrbnlulu/strawberry-django-auth/pull/516/)

0.376.8 - 2024-04-06
--------------------
This release improves the CD

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #515](https://github.com/nrbnlulu/strawberry-django-auth/pull/515/)

0.376.7 - 2024-04-03
--------------------

Fix channels support: Fixing side effects of changing the structure of a context object
Add gqlauth.settings_type.id_field to use in project settings

Contributed by [Hyun S. Moon](https://github.com/shmoon-kr) via [PR #504](https://github.com/nrbnlulu/strawberry-django-auth/pull/504/)


0.376.6 - 2024-03-28
--------------------

This release fixes mypy errors, updates linters, and added docs about `JwtSchema`.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #500](https://github.com/nrbnlulu/strawberry-django-auth/pull/500/)


0.376.5 - 2024-01-27
--------------------

Fix bug in removal of JWT prefix.
In the current implementation if a token happens to contain any trailing J, W or T chars they are also removed.
This fix ensures we're only interested in the prefix as a substring.

0.376.4 - 2023-12-09
--------------------

This release adds support for Django 5.0 (https://docs.djangoproject.com/en/5.0/releases/5.0/).

Contributed by [Babu Somasundaram](https://github.com/babus) via [PR #464](https://github.com/nrbnlulu/strawberry-django-auth/pull/464/)


0.376.3 - 2023-11-21
--------------------

This release adds support for Python3.12

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #459](https://github.com/nrbnlulu/strawberry-django-auth/pull/459/)


0.376.2 - 2023-08-15
--------------------

This release restores an accidentally deleted django migrations.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #430](https://github.com/nrbnlulu/strawberry-django-auth/pull/430/)


0.376.1 - 2023-08-14
--------------------

This release fixes the way we set the refresh token's field `revoked`.
Previously we were passing a naive DateTime object but now we pass the timestamp with the timezone info.

fixes #395

Contributed by [kurttsam](https://github.com/kurttsam) via [PR #424](https://github.com/nrbnlulu/strawberry-django-auth/pull/424/)


0.376.0 - 2023-08-07
--------------------

This release removes the call for `authenticate()` on basic JWT authorization in order
to support multiple authorization backends see issue #268.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #420](https://github.com/nrbnlulu/strawberry-django-auth/pull/420/)


0.375.0 - 2023-07-10
--------------------

This release updates to the latest version of strawberry
and removes dependencies with strawberry-django-plus.

- The directive `IsVerified` is migrated to the new field
extensions API and extends the django base permission
extension.

- The Channels middleware will inject the user in `request.user`
or `request.scope["UserOrError"]`

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #403](https://github.com/nrbnlulu/strawberry-django-auth/pull/403/)


0.374.6 - 2023-05-29
--------------------

This release fixes the way we call django's `send_mail()` previously
we were passing the `DjangoSetting` object directly, but now we pass its value.

fixes #387

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #391](https://github.com/nrbnlulu/strawberry-django-auth/pull/391/)


0.374.5 - 2023-05-16
--------------------

Dependencies update

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
