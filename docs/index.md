# Strawberry Graphql Auth
![Logo](./images/logo.png){ align=center }
*JWT Authentication / Authorization system for strawberry-django.*


[![Tests](https://img.shields.io/github/workflow/status/nrbnlulu/strawberry-django-auth/Run%20Tests?label=Tests&style=for-the-badge)](https://github.com/nrbnlulu/strawberry-django-auth/actions/workflows/tests.yml)
[![Codecov](https://img.shields.io/codecov/c/github/nrbnlulu/strawberry-django-auth?style=for-the-badge)](https://app.codecov.io/gh/nrbnlulu/strawberry-django-auth)
[![Pypi](https://img.shields.io/pypi/v/strawberry-django-auth.svg?style=for-the-badge&logo=appveyor)](https://pypi.org/project/strawberry-django-auth/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=for-the-badge&logo=appveyor)](https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md)
[![Pypi downloads](https://img.shields.io/pypi/dm/strawberry-django-auth?style=for-the-badge)](https://pypistats.org/packages/strawberry-django-auth)
[![Python versions](https://img.shields.io/pypi/pyversions/strawberry-django-auth?style=social)](https://pypi.org/project/strawberry-django-auth/)

---

## Demo

[![Demo Video](https://github.com/nrbnlulu/strawberry-django-auth/blob/main/demo.gif?raw=true)](https://github.com/nrbnlulu/strawberry-django-auth#demo)

## About


Abstract all the basic logic of handling user accounts out of your app,
so you don't need to think about it and can ==get you up and running faster==.

No lock-in. When you are ready to implement your own code or this package
is not up to your expectations , it's ^^easy to extend or switch to
your implementation^^.

---
## Goals
- Easy JWT authentication compatible with strawberry.
- Some boiler-plate mutations like register, login etc.

## Non-goals
- Permission handling - out of scope for this project, we just provide you a user in `info.context.request`.

## Features

* [x] Awesome docs!
* [x] Captcha validation
* [x] Async/Sync supported!
* [x] django-channels asgi support.
* [x] Works with ==default or custom== user model
* [x] Built-in JWT authentication.
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

---


You can now jump to the [Tutorial](tutorial.md).
