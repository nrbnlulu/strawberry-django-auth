# Django GraphQL Auth

[Django](https://github.com/django/django) registration and authentication with GraphQL.


[![downloads](https://img.shields.io/pypi/dm/strawberry-django-auth)](https://pypistats.org/packages/strawberry-django-auth)
[![Pypi](https://img.shields.io/pypi/v/strawberry-django-auth.svg)](https://pypi.org/project/strawberry-django-auth/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md)

---

## Demo

[![Demo Video](https://github.com/nrbnlulu/strawberry-django-auth/blob/main/demo.gif?raw=true)](https://github.com/nrbnlulu/strawberry-django-auth#demo)

## About

Abstract all the basic logic of handling user accounts out of your app,
so you don't need to think about it and can ==get up and running faster==.

No lock-in. When you are ready to implement your own code or this package
is not up to your expectations , it's ^^easy to extend or switch to
your implementation^^.

---

## Features

* [x] Awesome docs!
* [x] Captcha validation
* [x] Works with ==default or custom== user model
* [x] JWT authentication <small>(with [Strawberry Django JWT](https://github.com/KundaPanda/strawberry-django-jwt))</small>
* [x] User registration with email verification
* [x] Add secondary email, with email verification too
* [x] Resend activation email
* [x] Retrieve/Update user
* [x] Archive user
* [x] Permanently delete user or make it inactive
* [x] Turn archived user active again on login
* [x] Track user status <small>(archived, verified, secondary email)</small>
* [x] Password change
* [x] Password reset through email
* [x] Revoke user tokens on account archive/delete/password change/reset
* [x] All mutations return `success` and `errors`
* [x] Default email templates <small>(you will customize though)</small>
* [x] Customizable, no lock-in
* [x] Passwordless registration
* [ ] Currently, only mutations are compatible with [Relay](https://github.com/facebook/relay>)
* [ ] Async is not supported yet, but you expect this in the close future

---

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

Check the [installation guide](installation.md) or jump to the [quickstart](quickstart.md). Or if you prefer, browse the [api](api.md).
