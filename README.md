
![Tests](https://github.com/nrbnlulu/strawberry-django-auth/actions/workflows/tests.yml/badge.svg)
[![Pypi](https://img.shields.io/pypi/v/strawberry-django-auth.svg)](https://pypi.org/project/strawberry-django-auth/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md)
# Strawberry-django Auth
[Django](https://github.com/django/django) registration and authentication with [Strawberry](https://strawberry.rocks/).

## Demo

![Demo Video](https://github.com/nrbnlulu/strawberry-django-auth/blob/main/demo.gif)

## About
### This Library is the strawberry version of ![Django-graphql-auth](https://github.com/pedrobern/django-graphql-auth/).

Abstract all the basic logic of handling user accounts out of your app,
so you don't need to think about it and can **get up and running faster**.

No lock-in. When you are ready to implement your own code or this package
is not up to your expectations , it's *easy to extend or switch to
your implementation*.


## Documentation

### Docs can be found [here](https://nrbnlulu.github.io/strawberry-django-auth/)

## Features

* [x] [Awesome docs](https://nrbnlulu.github.io/strawberry-django-auth/):tada:
* [ ] Fully compatible with [Relay](https://github.com/facebook/relay>)
* [x] Works with **default or custom** user model
* [x] JWT authentication *(with [strawberry-django-jwt](https://github.com/KundaPanda/strawberry-django-jwt))*
* [x] User query with filters
* [x] User registration with email verification
* [x] Add secondary email, with email verification too
* [x] Resend activation email
* [x] Retrieve/Update user
* [x] Archive user
* [x] Permanently delete user or make it inactive
* [x] Turn archived user active again on login
* [x] Track user status (archived, verified, secondary email)
* [x] Password change
* [x] Password reset through email
* [x] Revoke user refresh tokens on account archive/delete/password change/reset
* [x] All mutations return `success` and `errors`
* [x] Default email templates *(you will customize though)*
* [x] Customizable, no lock-in.


### Full schema features

```python
import strawberry
from gqlauth.user import arg_mutations as mutations

@strawberry.type
class AuthMutation:
    register = mutations.Register.Field
    verify_account = mutations.VerifyAccount.Field
    resend_activation_email = mutations.ResendActivationEmail.Field
    send_password_reset_email = mutations.SendPasswordResetEmail.Field
    password_reset = mutations.PasswordReset.Field
    password_set = mutations.PasswordSet.Field
    password_change = mutations.PasswordChange.Field
    archive_account = mutations.ArchiveAccount.Field
    delete_account = mutations.DeleteAccount.Field
    update_account = mutations.UpdateAccount.Field
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.Field
    verify_secondary_email = mutations.VerifySecondaryEmail.Field
    swap_emails = mutations.SwapEmails.Field
    captcha = mutations.Cap.Field

    # django-graphql-jwt authentication
    # with some extra features
    token_auth = mutations.ObtainJSONWebToken.Field
    verify_token = mutations.VerifyToken.Field
    refresh_token = mutations.RefreshToken.Field
    revoke_token = mutations.RevokeToken.Field

schema = strawberry.Schema(mutation=AuthMutation)
```


## User relay queries

### Currently not supported
expect to find it here when strawberry will natively support relay


## Example

Handling user accounts becomes super easy.

```python
mutation {
  register(
    email: "new_user@email.com",
    username: "new_user",
    password1: "123456super",
    password2: "123456super",
  ) {
    success,
    errors,
    token,
    refreshToken
  }
}
```

Check the status of the new user:

```python
u = UserModel.objects.last()
u.status.verified
# False
```

During the registration, an email with a verification link was sent.

```python
mutation {
  verifyAccount(
    token:"<TOKEN ON EMAIL LINK>",
  ) {
    success,
    errors
  }
}
```

Now user is verified.

```python
u.status.verified
# True
```



## Contributing

See [CONTRIBUTING.md](https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md)
