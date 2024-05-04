## What to expect

- Fully functional API to handle user account
- Setup with custom user model
- 20 to 30 minutes

[Final code on github](https://github.com/nrbnlulu/strawberry-django-auth/tree/main/quickstart).

## Requirements

- Python: >= 3.8
- Django: >= 3.2
- Basic knowledge in [Strawberry](https://strawberry.rocks/)

---

## Start a new Django Project

!!! info ""
    It's recommended to use [virtual env wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/index.html) or [virtualenv](https://virtualenv.pypa.io/en/latest/) to create
    your project inside an isolated python environment. We will use the first.

### Create the virtual env

```bash
mkdir strawberry-django-auth-tutorial
cd strawberry-django-auth-tutorial
python -m venv venv
source venv/bin/activate
```

### Create the Django Project

First install django:

```bash
python -m pip install django
```

Then, create the new project. Take note of the "." at the end of the command, it will create the project in the current directory.:

```bash
django-admin startproject quickstart .
```

### Create the custom user model

Changing to a custom user model mid-project is significantly more difficult. So let's start by adding it now. Run the following:

```bash
python manage.py startapp users
```

Then, create the custom user model:

```python
# users/models.py

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    email = models.EmailField(blank=False, max_length=254, verbose_name="email address")

    USERNAME_FIELD = "username"   # e.g: "username", "email"
    EMAIL_FIELD = "email"         # e.g: "email", "primary_email"
```

Add it to the settings:

```python
# quickstart/settings.py

INSTALLED_APPS = [
    # ...
    'users'
]

AUTH_USER_MODEL = 'users.CustomUser'
```

Finally, migrate:

```bash
python manage.py makemigrations
python manage.py migrate
```

!!! info ""
    You can customize the mutations to match your custom user model fields, see the [dynamic-fields settings](settings.md#dynamic-fields).

---

## Install strawberry-django-auth

```bash
pip install strawberry-django-auth
```

```python
# quickstart/settings.py
from gqlauth.settings_type import GqlAuthSettings

INSTALLED_APPS = [
    # ...
    'django.contrib.staticfiles',  # Required for GraphiQL
    "strawberry_django",
    "gqlauth",

]

MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gqlauth.core.middlewares.django_jwt_middleware'
    # ...
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
```

We will disable captcha validation for now, just for ease of setup.

```py
# quickstart/settings.py
from gqlauth.settings_type import GqlAuthSettings

GQL_AUTH = GqlAuthSettings(
    LOGIN_REQUIRE_CAPTCHA=False,
    REGISTER_REQUIRE_CAPTCHA=False,
)
```

And make sure your templates configuration has the following:

```python
TEMPLATES = [
    {
        # ...
        'APP_DIRS': True,
    },
]
```

Run:

```bash
python -m manage migrate
```

---

## Create the schema

Create a file called `schema.py` next to your `models.py`

Add the following to code:

```py
# users/schema.py

import strawberry
from gqlauth.user.queries import UserQueries
from gqlauth.core.middlewares import JwtSchema

```

=== "Default"
    ```py
    from gqlauth.user import arg_mutations as mutations
    ```

=== "Relay"
    ```py
    from gqlauth.user import relay as mutations
    ```

```py

@strawberry.type
class Query(UserQueries):
    # you can add your queries here
    ...
```

??? Note "you can choose what fields to include like this"

  ```python
  import strawberry
  from gqlauth.user.queries import UserQueries, UserType
  from django.contrib.auth import get_user_model
  from gqlauth.core.middlewares import JwtSchema

  @strawberry.django.type(model=get_user_model())
  class MyQueries:
      me: UserType = UserQueries.me
      public: UserType = UserQueries.public_user
      # etc...
  ```

```py


@strawberry.type
class Mutation:

    # include what-ever mutations you want.
    verify_token = mutations.VerifyToken.field
    update_account = mutations.UpdateAccount.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    swap_emails = mutations.SwapEmails.field
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

# This is essentially the same as strawberries schema though it
# injects the user to `info.context["request"].user`
schema = JwtSchema(query=Query, mutation=Mutation)

```

## Update the urls

```python
# quickstart/urls.py
from strawberry.django.views import AsyncGraphQLView
from users.schema import schema

urlpatterns = [
  path("admin/", admin.site.urls),
  path('graphql', AsyncGraphQLView.as_view(schema=schema)),
]
```

---

## Load fixtures

Before starting to query, let's load some users on the database. Create a new file called ``users.json`` in the same directory as ``manage.py`` with the following:

!!! info ""
    Have a look on the fixtures, note that we are creating 4 users and 3 `UserStatus`. When creating a user, we create a relating `UserStatus` by default on `post_save` signal with the following fields:

  ```python
  verified=False
  archived=False
  ```

  You can access it on any user:

  ```bash
  user.status.[verified | archived]
  ```

```json
[
  {
      "model": "users.CustomUser",
      "pk": 1,
      "fields": {
          "password": "pbkdf2_sha256$180000$nFcBtiqGnWN9$hf58wNg77oT1BlNKRdATVVvBIa69+dz22fL1JKOKTaA=",
          "last_login": null,
          "is_superuser": false,
          "username": "user1",
          "first_name": "",
          "last_name": "",
          "email": "user1@email.com",
          "is_staff": false,
          "is_active": true
      }
  },
  {
      "model": "users.CustomUser",
      "pk": 2,
      "fields": {
          "password": "pbkdf2_sha256$180000$nFcBtiqGnWN9$hf58wNg77oT1BlNKRdATVVvBIa69+dz22fL1JKOKTaA=",
          "last_login": null,
          "is_superuser": false,
          "username": "user2",
          "first_name": "",
          "last_name": "",
          "email": "user2@email.com",
          "is_staff": false,
          "is_active": true
      }
  },
  {
      "model": "gqlauth.userstatus",
      "pk": 2,
      "fields": {
          "user": 2,
          "verified": true,
          "archived": false
      }
  },
  {
      "model": "users.CustomUser",
      "pk": 3,
      "fields": {
          "password": "pbkdf2_sha256$180000$nFcBtiqGnWN9$hf58wNg77oT1BlNKRdATVVvBIa69+dz22fL1JKOKTaA=",
          "last_login": null,
          "is_superuser": false,
          "username": "user3",
          "first_name": "",
          "last_name": "",
          "email": "user3@email.com",
          "is_staff": false,
          "is_active": true
      }
  },
  {
      "model": "gqlauth.userstatus",
      "pk": 3,
      "fields": {
          "user": 3,
          "verified": true,
          "archived": true
      }
  },
  {
      "model": "users.CustomUser",
      "pk": 4,
      "fields": {
          "password": "pbkdf2_sha256$180000$nFcBtiqGnWN9$hf58wNg77oT1BlNKRdATVVvBIa69+dz22fL1JKOKTaA=",
          "last_login": null,
          "is_superuser": false,
          "username": "user4",
          "first_name": "",
          "last_name": "",
          "email": "user4@email.com",
          "is_staff": false,
          "is_active": true
      }
  },
  {
      "model": "gqlauth.userstatus",
      "pk": 4,
      "fields": {
          "user": 4,
          "verified": true,
          "archived": false
      }
  }
]


```

run:

```bash
python -m  manage loaddata users.json
```

---

## Making your first query

Start the dev server:

```bash
python manage.py runserver
```

Open your browser:

```bash
http://127.0.0.1:8000/graphql
```

### First let's log-in

#### Setup Email Backend

The default configuration is to send activation email when registering users,
you can set it to `False` on your [settings](settings.md),
but you still need an Email Backend
to password reset.

The quickest solution for development is to set up a [Console Email Backend](https://docs.djangoproject.com/en/3.0/topics/email/#console-backend), simply add the following to your

```settings.py```.

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Now all emails are sent to the standard output, instead of an actual email, and we
are ready to continue this guide.


#### Let's try to register a new user:
!!! failure "Too weak password"
    === "gql"
        ```python hl_lines="5 6"
        mutation {
          register(
            email: "new_user@email.com",
            username: "new_user",
            password1: "123456",
            password2: "123456",
          ) {
            success,
            errors,
          }
        }
        ```
    === "relay"
        ```gql hl_lines="3 8"
        mutation {
          register(
            input: {
              email: "new_user@email.com",
              username: "new_user",
              password1: "123456",
              password2: "123456",
            }
          ) {
            success,
            errors,
            token,
            refreshToken
          }
        }
        ```
    === "response"
        ```json
            {
              "data": {
                "register": {
                  "success": false,
                  "errors": {
                    "password2": [
                      {
                        "message": "This password is too short. It must contain at least 8 characters.",
                        "code": "password_too_short"
                      },
                      {
                        "message": "This password is too common.",
                        "code": "password_too_common"
                      },
                      {
                        "message": "This password is entirely numeric.",
                        "code": "password_entirely_numeric"
                      }
                    ]
                  }
                }
              }
            }
        ```
Something went wrong! Now you know the response format that you can expect of
all mutations.

Let's try again:

!!! success "successful registration"
    === "arg_mutation"
        ```gql hl_lines="5 6"
        mutation {
          register(
            email: "new_user@email.com",
            username: "new_user",
            password1: "SuperSecureP@sw0rd",
            password2: "SuperSecureP@sw0rd",
          ) {
            success,
            errors,
            success
          }
        }
        ```
    === "relay"

        ```gql hl_lines="3 8"
        mutation {
          register(
            input: {
              email: "new_user@email.com",
              username: "new_user",
              password1: "SuperSecureP@sw0rd",
              password2: "SuperSecureP@sw0rd",
            }
          ) {
            success,
            errors,
            token,
            refreshToken
          }
        }
        ```

    === "response"
        ```json
        {
          "data": {
            "register": {
              "success": true,
              "errors": null
            }
          }
        }
        ```

There is actually a new user, it is possible to log in (you can change it on the [settings](settings.md)),
but it is not verified yet.

Save the `id` of the new user, so we can query it later.

Go to your console and note the email that has been sent. Should be two outputs, html and plain text formats.

Save the token from the url, something like this:

```bash
eyJ1c2VybmFtZSI6Im5ld191c2VyIiwiYWN0aW9uIjoiYWN0aXZhdGlvbiJ9:1isoSr:CDwK_fjBSxWj3adC-X16wqzv-Mw
```

#### Verify the new user

search your schema for ``verify_account``:
should look like this:
![Verify-account](images/verify-acount-screen-shot.png)

Now let's try to verify the account:

!!! gql
    === "arg_mutation"
        ```gql
        mutation {
          verifyAccount(token: "YOUR TOKEN HERE") {
            success,
            errors
          }
        }
        ```
    === "relay"
        ```python hl_lines="3 5"
            mutation {
              verifyAccount(
                input: {
                  token: "<YOUR TOKEN HERE>"
                }
              )
              {
                success,
                errors
              }
            }
        ```
    === "result"
        ```json
        {
          "data": {
            "verifyAccount": {
              "success": true,
              "errors": null
            }
          }
        }
        ```


#### Login

search your schema for `tokenAuth`:
should look like this:
![Verify-account](images/token-auth.png)

!!! gql
    === "arg_mutation"
        ```gql
        mutation {
          tokenAuth(username: "new_user", password: "SuperSecureP@sw0rd") {
            success
            errors
            token {
              payload {
                origIat
                exp
              }
              token
            }
            user {
              isActive
              username
              email
              status {
                verified
              }
            }
          }
        }
        ```
    === "relay"
        ```gql hl_lines="2"
        mutation {
          tokenAuth(input: {username: "new_user", password: "SuperSecureP@sw0rd"}) {
            success
            errors
            token {
              payload {
                origIat
                exp
              }
              token
            }
            user {
              isActive
              username
              email
              status {
                verified
              }
            }
          }
        }
        ```
    === "response"

        ```json
        {
          "data": {
            "tokenAuth": {
              "success": true,
              "errors": null,
              "token": {
                "payload": {
                  "origIat": "2022-09-18T14:56:33.829961",
                  "exp": "2022-09-18T15:01:33.829961"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXlsb2FkIjoie1xuIFwiZXhwXCI6IFwiMjAyMi0wOS0xOFQxNTowMTozMy44Mjk5NjFcIixcbiBcIm9yaWdJYXRcIjogXCIyMDIyLTA5LTE4VDE0OjU2OjMzLjgyOTk2MVwiLFxuIFwidXNlcm5hbWVcIjogXCJuZXdfdXNlclwiXG59In0.2qSD_203UCa4EmtiDz-YtbO59ETaLfLGj7R_6c2197Y"
              },
              "user": {
                "isActive": true,
                "username": "new_user",
                "email": "new_user@email.com",
                "status": {
                  "verified": true
                }
              }
            }
          }
        }
        ```



Save this `token`, we are going to use it in the request headers.

### MeQuery

With ``MeQuery`` you can retrieve data for the currently authenticated user:
!!! Fail "No headers supplied, will raise graphql error"
    === "query"
        ```graphql
            query{
              me{
                username
                verified
              }
            }
        ```
    === "response"
        ```json
        {
          "data": null,
          "errors": [
            {
              "message": "User is not authenticated.",
              "locations": [
                {
                  "line": 2,
                  "column": 3
                }
              ],
              "path": [
                "me"
              ]
            }
          ]
        }
        ```

!!! Success "With the token from last mutation, we can access the data. "
    Add The token in the Headers section in GraphiQL
    ![img.png](images/headers_graphiql.png)
    === "query"
        ```graphql
            query{
              me{
                username
                verified
              }
            }
        ```
    === "response"
        ```json
        {
          "data": {
            "me": {
              "verified": true,
              "username": "testadmin"
            }
          }
        }
        ```

!!! tip ""
    If it fails because of the token (in case you took some time, and it has expired), make the login again and get a new token.

---

## Next steps

- explore all the mutations.
- [Support Django-Channels](channels.md).
- Navigate through the GraphiQL Documentation Explorer.
- Change the [settings](settings.md).
- Explore the [api](api.md).
- make sure you are familiar with our [captcha](captcha.md) system.
- [Override email templates](overriding-email-templates.md).
