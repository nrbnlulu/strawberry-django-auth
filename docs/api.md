
> auto generated using `pydoc_markdown`
___
## asdict

## SMTPException

## Union

## UUID

## async\_to\_sync

## sync\_to\_async

## get\_user\_model

## PasswordChangeForm

## SetPasswordForm

## ObjectDoesNotExist

## BadSignature

## SignatureExpired

## transaction

## strawberry

## Info

## JSONWebTokenError

## JSONWebTokenExpired

## JwtObtainParent

## RefreshParent

## RevokeParent

## VerifyParent

## create\_user\_token

## MutationNormalOutput

## ObtainJSONWebTokenPayload

## RefreshTokenPayload

## RevokeTokenPayload

## VerifyTokenPayload

## Messages

## TokenAction

## \_password\_confirmation\_required

## secondary\_email\_required

## verification\_required

## EmailAlreadyInUse

## InvalidCredentials

## PasswordAlreadySetError

## TokenScopeError

## UserAlreadyVerified

## UserNotVerified

## EmailForm

## PasswordLessRegisterForm

## RegisterForm

## UpdateAccountForm

## CaptchaModel

## UserStatus

## app\_settings

## get\_user\_by\_email

## get\_user\_to\_login

## user\_registered

## user\_verified

## CaptchaType

## g\_user

## get\_payload\_from\_token

## inject\_fields

## revoke\_user\_refresh\_token

## UserModel

## Captcha

```python
class Captcha()
```

> Creates a brand-new captcha.
> Returns a base64 encoded string of the captcha.
> And uuid representing the captcha id in the database.
> When you will try to log in or register You will
> need submit that uuid With the user input.
> **The captcha will be invoked when the timeout expires**.

### field

```python
@strawberry.mutation(description=__doc__)
def field() -> CaptchaType
```

### afield

```python
@strawberry.mutation(description=__doc__)
@sync_to_async
def afield() -> CaptchaType
```

## check\_captcha

```python
def check_captcha(
    input_: Union["RegisterMixin.RegisterInput",
                  "ObtainJSONWebTokenMixin.ObtainJSONWebTokenInput"])
```

## RegisterMixin

```python
class RegisterMixin()
```

> Register user with fields defined in the settings.
> If the email field of the user model is part of the
> registration fields (default), check if there is
> no user with that email or as a secondary email.
>
> If it exists, it does not register the user,
> even if the email field is not defined as unique
> (default of the default django user model).
>
> When creating the user, it also creates a `UserStatus`
> related to that user, making it possible to track
> if the user is archived, verified and has a secondary
> email.
>
> Send account verification email.
>
> If allowed to not verified users login, return token.

### RegisterInput

```python
@strawberry.input

@inject_fields(app_settings.REGISTER_MUTATION_FIELDS)
class RegisterInput()
```

### form

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, info, input_: RegisterInput) -> MutationNormalOutput
```

## VerifyAccountMixin

```python
class VerifyAccountMixin()
```

> Verify user account.
>
> Receive the token that was sent by email.
> If the token is valid, make the user verified
> by making the `user.status.verified` field true.

### VerifyAccountInput

```python
@strawberry.input
class VerifyAccountInput()
```

#### token

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, info: Info,
                     input_: VerifyAccountInput) -> MutationNormalOutput
```

## VerifySecondaryEmailMixin

```python
class VerifySecondaryEmailMixin()
```

> Verify user secondary email.
>
> Receive the token that was sent by email.
> User is already verified when using this mutation.
>
> If the token is valid, add the secondary email
> to `user.status.secondary_email` field.
>
> Note that until the secondary email is verified,
> it has not been saved anywhere beyond the token,
> so it can still be used to create a new account.
> After being verified, it will no longer be available.

### VerifySecondaryEmailInput

```python
@strawberry.input
class VerifySecondaryEmailInput()
```

#### token

### resolve\_mutation

```python
@classmethod
def resolve_mutation(
        cls, _, input_: VerifySecondaryEmailInput) -> MutationNormalOutput
```

## ResendActivationEmailMixin

```python
class ResendActivationEmailMixin()
```

> Sends activation email.
>
> It is called resend because theoretically
> the first activation email was sent when
> the user registered.
>
> If there is no user with the requested email,
> a successful response is returned.

### ResendActivationEmailInput

```python
@strawberry.input
class ResendActivationEmailInput()
```

#### email

### resolve\_mutation

```python
@classmethod
def resolve_mutation(
        cls, info, input_: ResendActivationEmailInput) -> MutationNormalOutput
```

## SendPasswordResetEmailMixin

```python
class SendPasswordResetEmailMixin()
```

> Send password reset email.
>
> For non verified users, send an activation
> email instead.
>
> Accepts both primary and secondary email.
>
> If there is no user with the requested email,
> a successful response is returned.

### SendPasswordResetEmailInput

```python
@strawberry.input
class SendPasswordResetEmailInput()
```

#### email

### resolve\_mutation

```python
@classmethod
def resolve_mutation(
        cls, info,
        input_: SendPasswordResetEmailInput) -> MutationNormalOutput
```

## PasswordResetMixin

```python
class PasswordResetMixin()
```

> Change user password without old password.
>
> Receive the token that was sent by email.
>
> If token and new passwords are valid, update
> user password and in case of using refresh
> tokens, revoke all of them.
>
> Also, if user has not been verified yet, verify it.

### PasswordResetInput

```python
@strawberry.input
class PasswordResetInput()
```

#### token

#### new\_password1

#### new\_password2

### form

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, _,
                     input_: PasswordResetInput) -> MutationNormalOutput
```

## PasswordSetMixin

```python
class PasswordSetMixin()
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

### PasswordSetInput

```python
@strawberry.input
class PasswordSetInput()
```

#### token

#### new\_password1

#### new\_password2

### form

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, _, input_: PasswordSetInput) -> MutationNormalOutput
```

## ObtainJSONWebTokenMixin

```python
class ObtainJSONWebTokenMixin()
```

> Obtain JSON web token for given user.
>
> Allow to perform login with different fields,
> and secondary email if set. The fields are
> defined on settings.
>
> Not verified users can log in by default. This
> can be changes on settings.
>
> If user is archived, make it unarchived and
> return `unarchiving=True` on OutputBase.

### ObtainJSONWebTokenInput

```python
@strawberry.input

@inject_fields(app_settings.LOGIN_FIELDS)
class ObtainJSONWebTokenInput()
```

#### password

### resolve\_mutation

```python
@classmethod
def resolve_mutation(
        cls, info,
        input_: ObtainJSONWebTokenInput) -> ObtainJSONWebTokenPayload
```

## ArchiveOrDeleteMixin

```python
class ArchiveOrDeleteMixin()
```

### ArchiveOrDeleteMixinInput

```python
@strawberry.input
class ArchiveOrDeleteMixinInput()
```

#### password

### resolve\_mutation

```python
@classmethod
@verification_required
@_password_confirmation_required
def resolve_mutation(
        cls, info, input_: ArchiveOrDeleteMixinInput) -> MutationNormalOutput
```

## ArchiveAccountMixin

```python
class ArchiveAccountMixin(ArchiveOrDeleteMixin)
```

> Archive account and revoke refresh tokens.
> User must be verified and confirm password.

### resolve\_action

```python
@classmethod
def resolve_action(cls, user)
```

## DeleteAccountMixin

```python
class DeleteAccountMixin(ArchiveOrDeleteMixin)
```

> Delete account permanently or make `user.is_active=False`.
>
> The behavior is defined on settings.
> Anyway user refresh tokens are revoked.
>
> User must be verified and confirm password.

### resolve\_action

```python
@classmethod
def resolve_action(cls, user)
```

## PasswordChangeMixin

```python
class PasswordChangeMixin()
```

> Change account password when user knows the old password.
>
> A new token and refresh token are sent. User must be verified.

### PasswordChangeInput

```python
@strawberry.input
class PasswordChangeInput()
```

#### old\_password

#### new\_password1

#### new\_password2

### form

### resolve\_mutation

```python
@classmethod
@verification_required
@_password_confirmation_required
def resolve_mutation(cls, info: Info,
                     input_: PasswordChangeInput) -> ObtainJSONWebTokenPayload
```

## UpdateAccountMixin

```python
class UpdateAccountMixin()
```

> Update user model fields, defined on settings.
>
> User must be verified.

### UpdateAccountInput

```python
@strawberry.input

@inject_fields(app_settings.UPDATE_MUTATION_FIELDS)
class UpdateAccountInput()
```

### form

### resolve\_mutation

```python
@classmethod
@verification_required
def resolve_mutation(cls, info,
                     input_: UpdateAccountInput) -> MutationNormalOutput
```

## VerifyTokenMixin

```python
class VerifyTokenMixin()
```

> Checks if a token is not expired and correct

### VerifyTokenInput

```python
@strawberry.input
class VerifyTokenInput()
```

#### token

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, info,
                     input_: VerifyTokenInput) -> VerifyTokenPayload
```

## RefreshTokenMixin

```python
class RefreshTokenMixin()
```

> ### refreshToken to refresh your token:
>
> using the refresh token you already got during authorization.
> this will obtain a brand-new token (and possibly a refresh token)
> with renewed expiration time for non-expired tokens

### RefreshTokenInput

```python
@strawberry.input
class RefreshTokenInput()
```

#### refresh\_token

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, info,
                     input_: RefreshTokenInput) -> RefreshTokenPayload
```

## RevokeTokenMixin

```python
class RevokeTokenMixin()
```

> Suspends a refresh token

### RevokeTokenInput

```python
@strawberry.input
class RevokeTokenInput()
```

#### refresh\_token

### resolve\_mutation

```python
@classmethod
def resolve_mutation(cls, info,
                     input_: RevokeTokenInput) -> RevokeTokenPayload
```

## SendSecondaryEmailActivationMixin

```python
class SendSecondaryEmailActivationMixin()
```

> Send activation to secondary email.
>
> User must be verified and confirm password.

### SendSecondaryEmailActivationInput

```python
@strawberry.input
class SendSecondaryEmailActivationInput()
```

#### password

### resolve\_mutation

```python
@classmethod
@verification_required
@_password_confirmation_required
def resolve_mutation(
        cls, info,
        input_: SendSecondaryEmailActivationInput) -> MutationNormalOutput
```

## SwapEmailsMixin

```python
class SwapEmailsMixin()
```

> Swap between primary and secondary emails.
>
> Require password confirmation.

### SwapEmailsInput

```python
@strawberry.input
class SwapEmailsInput()
```

#### password

### resolve\_mutation

```python
@classmethod
@secondary_email_required
def resolve_mutation(cls, info: Info,
                     input_: SwapEmailsInput) -> MutationNormalOutput
```

## RemoveSecondaryEmailMixin

```python
class RemoveSecondaryEmailMixin()
```

> Remove user secondary email.
>
> Require password confirmation.

### RemoveSecondaryEmailInput

```python
@strawberry.input
class RemoveSecondaryEmailInput()
```

#### password

### resolve\_mutation

```python
@classmethod
@secondary_email_required
@_password_confirmation_required
def resolve_mutation(
        cls, info: Info,
        input_: RemoveSecondaryEmailInput) -> MutationNormalOutput
```
