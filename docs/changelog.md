
# Changelog

### v0.3.3.2

- **New features**
  - Any fields that are in either
    `UPDATE_MUTATION_FIELDS`,
    `REGISTER_MUTATION_FIELDS`,
    `REGISTER_MUTATION_FIELDS_OPTIONAL`
     And the pk field of the model.
     Will be inserted to UserType and will be in user queries.
  - Doc strings in gqlquth_settings object
- **Bug fixed**
  - Issue #45, #42
    - `LOGIN_REQUIRED_FIELDS` is now supported,\
       These fields would be used to authenticate with SD-jwt `authenticate` function.
       This function will call each of our `AUTHENTICATION_BACKENDS`,
       And will return the user from one of them unless `PermissionDenied` was raised.

    - `REGISTER_MUTATION_FIELDS` is now supported,\
    Fields that will be registered there will be required by Register mutation

- **Development Notes**
    - Added new marker for pytest, `default_user` this is the user defined in the default
      settings, And the custom user is in `settings_b.py` with no email field.

### v0.3.3.1 - pre-release

- **New features**
  - async support using ASGI, the resolvers are still sync because of django's ORM
  -
- **API changes**
  - Previously, following the graphene version, we did i.e ` token_auth = relay.ObtainJSONWebToken.Field`,\
    In order to respect pep8 (since it is a function)\
    and Strawberry style we changed it to ` token_auth = relay.ObtainJSONWebToken.field`.
  - Renamed `Cap.Field` to `Captcha.field`.

- **Deprecations**
  - Removed setting ASYNC_EMAIL_TASK, (originally this was a celery task).

- **Development Notes**
  - Major refactoring of how the test work:
    - removed all the dicts that was flying around and used dataclasses.
    - added async tests for all tests.
    - no longer using request factory, now using test client as it emulates more real life environment.

### v0.3.16

- Nothing new, adding `PyJWT<=2.0.0` to requirements

### v0.3.15

- Emit `user_verified` signal on password reset (thanks to [@imsheldon](https://github.com/imsheldon))

### v0.3.14

- Add passwordless registration (thanks to [@joshuachinemezu](https://github.com/joshuachinemezu))
- Add `user_verified` and `user_registered` signals (thanks to [@mnieber](https://github.com/mnieber))
- Verify user in password reset mutation (thanks to [capaci ](https://github.com/capaci))

### v0.3.13

- Add EMAIL_TEMPLATE_VARIABLES setting (thanks to [capaci ](https://github.com/capaci))

### v0.3.12

- Add CUSTOM_ERROR_TYPE setting (thanks to [boolangery ](https://github.com/boolangery))

### v0.3.11

- Add select_related to UserNode to limit db queries (thanks to [maxpeterson](https://github.com/maxpeterson))

### v0.3.10

- Pseudo async email support (thanks to [bzhr](https://github.com/bzhr) and [me](https://github.com/nrbnlulu))

### v0.3.9

- Prevents that UserNode is registered globally for the User type (thanks to [panosangelopoulos](https://github.com/panosangelopoulos))

### v0.3.8

- Add request and timestamp to email templates (thanks to [yanivtoledano](https://github.com/yanivtoledano))

### v0.3.7

- Add template variables to email subjects.

### v0.3.6

- Replace RemovedInDjango40Warning ugettext with gettext (thanks to [ulgens](https://github.com/ulgens))

### v0.3.5

- Added `MeQuery` (thanks to [pors](https://github.com/pors)).

### v0.3.4

- Renamed from `ErrorType` to`ExpectedErrorType`, preventing clash with a `strawberry.django` type with same name..

### v0.3.3

- Fixed bug when performing login in `PasswordChangeMixin` (thanks to [panosangelopoulos](https://github.com/panosangelopoulos)).

### v0.3.2

- Fixed typo in error code/message for `expired_token` (thanks to [yanivtoledano](https://github.com/yanivtoledano)).

### v0.3.1

- add pk to UserNode.

### v0.3.0

- release beta.

## v0.2

### v0.2.8

- return new token and refreshToken on password change.

### v0.2.7

- allow login on register, returning token and refresh token.

### v0.2.6

- review error fields in some mutations.

### v0.2.5

- update apps config.
- nothing new.

### v0.2.4

- add mutation to remove secondary email.

### v0.2.3

- user status is created on signal.

### v0.2.2

- fix typo in setup.
- nothing new.

### v0.2.1

- fix readme on pypi.
- nothing new.

### v0.2.0

- minor bug fixes.
- add user status model to track if user is archived, verified and secondary email.
- add new mutations to handle secondary email.
- allow login with secondary email.

## v0.1

### 0.1.11

- Fix minor bugs.

### 0.1.10

- Fix minor bugs.

### 0.1.9

- Rename settings params.

### 0.1.8

- Fix typo in settings.

### 0.1.7

- No changes (testing release on Travis).

### 0.1.6

- Support for Django >= 2.1

### 0.1.5

- Revoke refresh tokens when archiving user.

### 0.1.4

- Allow to revoke refresh tokens on password change and reset.

### 0.1.3

- Better settings api.

### 0.1.2

- Update setup.py.

### 0.1.1

- Add initial README file!

### 0.1.0

- Hello world!
