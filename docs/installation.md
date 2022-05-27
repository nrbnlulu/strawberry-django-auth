# Installation

!!! attention
    If you are not familiarized with
    [Strawberry](https://strawberry.rocks/)
    or [Strawberry Django JWT](https://github.com/KundaPanda/strawberry-django-jwt), skip this
    installation section and go to the [quickstart](quickstart.md) guide.

---

## Requirements

- Python: 3.10
- Django:  4.0

---

## Installation

```bash
pip install strawberry-django-auth
```

!!! Note ""
    For those that are not installed, this will automatically install `strawberry`, `strawberry-django`,
    `strawberry-django-jwt`, `django`.

Add `gqlauth` to installed apps.

```python
INSTALLED_APPS = [
    # ...
    "gqlauth"
]
```

Migrate:

```bash
python manage.py migrate
```

---

## Setup

The following are the minimum steps required to get it running. It should not take more than 10 minutes.

---

### 1. Schema

#### In your schema add the following:

!!! Schema

    ```py
    # yourapp/users/schema.py

    import strawberry
    from gqlauth.user.queries import UserQueries
    ```
    === "GraphQl"
        ```py

        from gqlauth.user import arg_mutations

        @strawberry.type
        class UserMutations:
            token_auth = arg_mutations.ObtainJSONWebToken.Field # login mutation
            verify_token = arg_mutations.VerifyToken.Field
            refresh_token = arg_mutations.RefreshToken.Field
            revoke_token = arg_mutations.RevokeToken.Field
            register = arg_mutations.Register.Field
            verify_account = arg_mutations.VerifyAccount.Field
            update_account = arg_mutations.UpdateAccount.Field
            resend_activation_email = arg_mutations.ResendActivationEmail.Field
            archive_account = arg_mutations.ArchiveAccount.Field
            delete_account = arg_mutations.DeleteAccount.Field
            password_change = arg_mutations.PasswordChange.Field
            send_password_reset_email = arg_mutations.SendPasswordResetEmail.Field
            password_reset = arg_mutations.PasswordReset.Field
            password_set = arg_mutations.PasswordSet.Field
            verify_secondary_email = arg_mutations.VerifySecondaryEmail.Field
            swap_emails = arg_mutations.SwapEmails.Field
            remove_secondary_email = arg_mutations.RemoveSecondaryEmail.Field
            send_secondary_email_activation = arg_mutations.SendSecondaryEmailActivation.Field
        ```

    === "Relay"
    
        ```py
        from gqlauth.user import relay
        
        @strawberry.type
        class UserMutations:
            token_auth = relay.ObtainJSONWebToken.Field  # login mutation
            verify_token = relay.VerifyToken.Field
            refresh_token = relay.RefreshToken.Field
            revoke_token = relay.RevokeToken.Field
            register = relay.Register.Field
            verify_account = relay.VerifyAccount.Field
            update_account = relay.UpdateAccount.Field
            resend_activation_email = relay.ResendActivationEmail.Field
            archive_account = relay.ArchiveAccount.Field
            delete_account = relay.DeleteAccount.Field
            password_change = relay.PasswordChange.Field
            send_password_reset_email = relay.SendPasswordResetEmail.Field
            password_reset = relay.PasswordReset.Field
            password_set = relay.PasswordSet.Field
            verify_secondary_email = relay.VerifySecondaryEmail.Field
            swap_emails = relay.SwapEmails.Field
            remove_secondary_email = relay.RemoveSecondaryEmail.Field
            send_secondary_email_activation = relay.SendSecondaryEmailActivation.Field
        ```
    ```py
    # yourapp/schema.py

    import strawberry
    from strawberry.tools import merge_types
    from users.schema import UserMutations, UserQueries
    
    Query = merge_types("RootQuery", (UserQueries,))

    Mutation = merge_types("RootMutation", (UserMutations,))
    
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    ```

---

### 2. Allow Any Classes
Please refer to [strawberry-django-jwt](https://github.com/KundaPanda/strawberry-django-jwt#known-issues). 
as it is not trivially possible with strawberry.

---

### 3. Authentication Backend <small>- optional</small>

Add the following to your `#!python AUTHENTICATION_BACKENDS`:

```python
AUTHENTICATION_BACKENDS = [
    # remove this
    # "strawberry_django_jwt.backends.JSONWebTokenBackend",

    # add this
    "gqlauth.backends.GraphQLAuthBackend",

    # ...
]
```

!!! attention "What's the difference from the strawberry_django_jwt.backend?"
    We implement the same backend with only one difference:

    - It will not raise if you send a request with bad token to a class that is not on `#!python JWT_ALLOW_ANY_CLASSES`.

    ---

    Why should I want this behaivor?

    Intead of raising an actual error, we can handle it and return whatever make sense, e.g.:
    ```python
      cls(success=False errors="Unauthenticated.")
    ```

    ---

    You should handle this situation doing one of the following:

    - Simply use the strawberry_django_jwt decorator [@login_required](https://github.com/KundaPanda/strawberry-django-jwt/blob/e7f920ceade51fa32fb361fdb789ec03ffd558af/strawberry_django_jwt/decorators.py#L100).
    - Use [our login_required decorator](decorators.md#login_required), note that this expect your output to contain [this output](https://github.com/nrbnlulu/strawberry-django-auth/blob/9287d7e4c774e585de8852c14e18c3a9f8c70d97/gqlauth/bases/interfaces.py#L8).
    - Create your own login_required decorator!

---

### 4. Refresh Token <small>- optional</small>
!!! explanation 
    Refresh tokens are consept of jwt-web-tokens 
    what they mean is that every x time a so called *logged user* will need to request for a new token from the server
    and generally there are two types of them:  

    1. [Single token refresh](https://django-graphql-jwt.domake.io/refresh_token.html#single-token-refresh) *(and thats the default)*  

    2. [Long running refresh tokens](https://django-graphql-jwt.domake.io/refresh_token.html#long-running-refresh-tokens)  


    === "Single token refresh" 
        they will require the user to ask for refresh token every 5 minutes
        !!! warning
            most importantly won't use the database therefore ==it is not state-less==
        for more information head to [Django GraphQL JWT](https://django-graphql-jwt.domake.io/refresh_token.html)
    === "Long running refresh tokens"
        they will require the database (threfore migration) are state-less
        
        you should probably follow [Django GraphQL JWT](https://django-graphql-jwt.domake.io/refresh_token.html) docs for more information docs :wink: 
        but here is a TL;DR: to set this up:
        ```py
        INSTALLED_APPS = [
            # ...
            "strawberry_django_jwt.refresh_token",
        ]
        
        GRAPHQL_JWT = {
            # ...
            "JWT_VERIFY_EXPIRATION": True,
            "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
            "JWT_EXPIRATION_DELTA": timedelta(minutes=5),
            "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
        }
        ```
        And remember to migrate:
        ```bash
        python -m manage migrate
        ```

---

### 5. Email Templates

!!! Note ""
    Overriding email templates is covered [here](overriding-email-templates.md).

This package comes with some default email templates, if you plan to use it, make sure your templates configuration has the following:

```python
TEMPLATES = [
    {
        # ...
        'APP_DIRS': True,
    },
]
```

---

### 6. Email Backend

The default configuration is to send activation email,
you can set it to ``False`` on your [settings](settings.md),
but you still need an Email Backend
to password reset.

The quickest way for development is to setup a [Console Email Backend](https://docs.djangoproject.com/en/4.0/topics/email/#console-backend), simply add the following to your ```settings.py```.

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Now all emails are sent to the standard output, instead of an actual email.

---
