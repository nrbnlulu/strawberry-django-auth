[![Tests](https://img.shields.io/github/actions/workflow/status/nrbnlulu/strawberry-django-auth/tests.yml?label=Tests&style=for-the-badge)](https://github.com/nrbnlulu/strawberry-django-auth/actions/workflows/tests.yml)
[![Codecov](https://img.shields.io/codecov/c/github/nrbnlulu/strawberry-django-auth?style=for-the-badge)](https://app.codecov.io/gh/nrbnlulu/strawberry-django-auth)
[![Pypi](https://img.shields.io/pypi/v/strawberry-django-auth.svg?style=for-the-badge&logo=appveyor)](https://pypi.org/project/strawberry-django-auth/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=for-the-badge&logo=appveyor)](https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md)
[![Pypi downloads](https://img.shields.io/pypi/dm/strawberry-django-auth?style=for-the-badge)](https://pypistats.org/packages/strawberry-django-auth)
[![Python versions](https://img.shields.io/pypi/pyversions/strawberry-django-auth?style=social)](https://pypi.org/project/strawberry-django-auth/)

# Strawberry-django Auth
[Django](https://github.com/django/django) registration and authentication with [Strawberry](https://strawberry.rocks/).

## Demo

![Demo Video](https://github.com/nrbnlulu/strawberry-django-auth/blob/main/demo.gif)

## About
#### This Library was inspired by [Django-graphql-auth](https://github.com/pedrobern/django-graphql-auth/).

Abstract all the basic logic of handling user accounts out of your app,
so you don't need to think about it and can **get you up and running faster**.

No lock-in. When you are ready to implement your own code or this package
is not up to your expectations , it's *easy to extend or switch to
your implementation*.


### Docs can be found [here](https://nrbnlulu.github.io/strawberry-django-auth/)

## Features

* [x] Awesome docs!
* [x] Captcha validation
* [x] Async/Sync supported!
* [x] Works with default or custom user model
* [x] Builtin JWT authentication using [PyJWT](https://github.com/jpadilla/pyjwt)
* [x] User registration with email verification
* [x] Retrieve/Update user
* [x] Archive user
* [x] Permanently delete user or make it inactive
* [x] Turn archived user active again on login
* [x] Track user status <small>(archived, verified)</small>
* [x] Password change
* [x] Password reset through email
* [x] Revoke user tokens on account archive/delete/password change/reset
* [x] All mutations return `success` and `errors`
* [x] Default email templates <small>(you will customize though)</small>
* [x] Customizable, no lock-in
* [x] Passwordless registration


### Full schema features

```python

@strawberry.type
class AuthMutation:
    # include here your mutations that interact with a user object from a token.

    verify_token = mutations.VerifyToken.field
    update_account = mutations.UpdateAccount.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    swap_emails = mutations.SwapEmails.field

@strawberry.type
class Mutation:
    @field(directives=[TokenRequired()])
    def auth_entry(self) -> Union[AuthMutation, GQLAuthError]:
        return AuthOutput(node=AuthMutation())

    # these are mutation that does not require authentication.
    captcha = Captcha.field
    token_auth = mutations.ObtainJSONWebToken.field
    register = mutations.Register.field
    verify_account = mutations.VerifyAccount.field
    resend_activation_email = mutations.ResendActivationEmail.field
    send_password_reset_email = mutations.SendPasswordResetEmail.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field
    verify_secondary_email = mutations.VerifySecondaryEmail.field


schema = strawberry.Schema(query=Query, mutation=Mutation)

```

## Contributing

See [CONTRIBUTING.md](https://github.com/nrbnlulu/strawberry-django-auth/blob/main/CONTRIBUTING.md)
