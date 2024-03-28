
> auto generated using `pydoc_markdown`
___
## RegisterMixin

```python
class RegisterMixin(BaseMixin)
```

> Register user with fields defined in the settings. If the email field of
> the user model is part of the registration fields (default), check if there
> is no user with that email.
>
> If it exists, it does not register the user, even if the email field
> is not defined as unique (default of the default django user model).
>
> When creating the user, it also creates a `UserStatus` related to
> that user, making it possible to track if the user is archived /
> verified.
>
> Send account verification email.
>
> If allowed to not verified users login, return token.

## VerifyAccountMixin

```python
class VerifyAccountMixin(BaseMixin)
```

> Verify user account.
>
> Receive the token that was sent by email. If the token is valid,
> make the user verified by making the `user.status.verified` field
> true.

## ResendActivationEmailMixin

```python
class ResendActivationEmailMixin(BaseMixin)
```

> Sends activation email.
>
> It is called resend because theoretically the first activation email
> was sent when the user registered.
>
> If there is no user with the requested email, a successful response
> is returned.

## SendPasswordResetEmailMixin

```python
class SendPasswordResetEmailMixin(BaseMixin)
```

> Send password reset email.
>
> For non verified users, send an activation email instead.
>
> If there is no user with the requested email, a successful response
> is returned.

## PasswordResetMixin

```python
class PasswordResetMixin(BaseMixin)
```

> Change user password without old password.
>
> Receive the token that was sent by email.
>
> If token and new passwords are valid, update user password and in
> case of using refresh tokens, revoke all of them.
>
> Also, if user has not been verified yet, verify it.

## PasswordSetMixin

```python
class PasswordSetMixin(BaseMixin)
```

> Set user password - for password-less registration
>
> Receive the token that was sent by email.
>
> If token and new passwords are valid, set
> user password and in case of using refresh
> tokens, revoke all of them.
>
> Also, if user has not been verified yet, verify it.

## ObtainJSONWebTokenMixin

```python
class ObtainJSONWebTokenMixin(BaseMixin)
```

> Obtain JSON web token for given user.
>
> Allow to perform login with different fields, The fields are defined
> on settings.
>
> Not verified users can log in by default. This can be changes on
> settings.
>
> If user is archived, make it unarchived and return
> `unarchiving=True` on OutputBase.

## ArchiveAccountMixin

```python
class ArchiveAccountMixin(ArchiveOrDeleteMixin)
```

> Archive account and revoke refresh tokens.
>
> User must be verified and confirm password.

## DeleteAccountMixin

```python
class DeleteAccountMixin(ArchiveOrDeleteMixin)
```

> Delete account permanently or make `user.is_active=False`.
>
> The behavior is defined on settings. Anyway user refresh tokens are
> revoked.
>
> User must be verified and confirm password.

## PasswordChangeMixin

```python
class PasswordChangeMixin(BaseMixin)
```

> Change account password when user knows the old password.
>
> A new token and refresh token are sent. User must be verified.

## UpdateAccountMixin

```python
class UpdateAccountMixin(BaseMixin)
```

> Update user model fields, defined on settings.
>
> User must be verified.

## VerifyTokenMixin

```python
class VerifyTokenMixin(BaseMixin)
```

> ### Checks if a token is not expired and correct.
>
> *Note that this is not for refresh tokens.*

## RefreshTokenMixin

```python
class RefreshTokenMixin(BaseMixin)
```

> ### refreshToken to generate a new login token:
>
> *Use this only if `JWT_LONG_RUNNING_REFRESH_TOKEN` is True*
>
> using the refresh-token you already got during authorization, and
> obtain a brand-new token (and possibly a new refresh token if you
> revoked the previous). This is an alternative to log in when your
> token expired.

## RevokeTokenMixin

```python
class RevokeTokenMixin(BaseMixin)
```

> ### Suspends a refresh token.
>
> *token must exist to be revoked.*
