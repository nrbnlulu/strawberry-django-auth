|Tests| |Pypi| |contributions welcome| # Strawberry-django Auth
`Django <https://github.com/django/django>`__ registration and
authentication with `Strawberry <https://strawberry.rocks/>`__.

Demo
----

.. figure:: https://github.com/nrbnlulu/strawberry-django-auth/blob/main/demo.gif
   :alt: Demo Video

   Demo Video

About
-----

This Library is the strawberry version of |Django-graphql-auth|.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Abstract all the basic logic of handling user accounts out of your app,
so you don’t need to think about it and can **get up and running
faster**.

No lock-in. When you are ready to implement your own code or this
package is not up to your expectations , it’s *easy to extend or switch
to your implementation*.

Documentation
-------------

Documentation is available at `read the
docs <https://strawberry-django-auth.readthedocs.io/en/latest/>`__.

Features
--------

-  ☐ `Awesome
   docs <https://strawberry-django-auth.readthedocs.io/en/latest/>`__:tada:
-  ☐ Fully compatible with
   `Relay <https://github.com/facebook/relay%3E>`__
-  ☒ Works with **default or custom** user model
-  ☒ JWT authentication
   *(with*\ `strawberry-django-jwt <https://github.com/KundaPanda/strawberry-django-jwt>`__\ *)*
-  ☒ User query with filters *(with*\ `Django
   Filter <https://github.com/carltongibson/django-filter>`__\ *and*\ `Graphene
   Django <https://github.com/graphql-python/graphene-django>`__\ *)*
-  ☒ User registration with email verification
-  ☒ Add secondary email, with email verification too
-  ☒ Resend activation email
-  ☒ Retrieve/Update user
-  ☒ Archive user
-  ☒ Permanently delete user or make it inactive
-  ☒ Turn archived user active again on login
-  ☒ Track user status (archived, verified, secondary email)
-  ☒ Password change
-  ☒ Password reset through email
-  ☒ Revoke user refresh tokens on account archive/delete/password
   change/reset
-  ☒ All mutations return ``success`` and ``errors``
-  ☒ Default email templates *(you will customize though)*
-  ☒ Customizable, no lock-in.

Full schema features
~~~~~~~~~~~~~~~~~~~~

.. code:: python

   import strawberry
   from gqlauth.user import arg_mutations


   @strawberrry.type
   class AuthMutation:
       register = mutations.Register.Field
       verify_account = mutations.VerifyAccount.Field
       resend_activation_email = mutations.ResendActivationEmail.Field
       send_password_reset_email = mutations.SendPasswordResetEmail.Field
       password_reset = mutations.PasswordReset.Field
       password_set = mutations.PasswordSet.Field # For passwordless registration
       password_change = mutations.PasswordChange.Field
       update_account = mutations.UpdateAccount.Field
       archive_account = mutations.ArchiveAccount.Field
       delete_account = mutations.DeleteAccount.Field
       send_secondary_email_activation =  mutations.SendSecondaryEmailActivation.Field
       verify_secondary_email = mutations.VerifySecondaryEmail.Field
       swap_emails = mutations.SwapEmails.Field
       remove_secondary_email = mutations.RemoveSecondaryEmail.Field

       # django-graphql-jwt inheritances
       token_auth = mutations.ObtainJSONWebToken.Field
       verify_token = mutations.VerifyToken.Field
       refresh_token = mutations.RefreshToken.Field
       revoke_token = mutations.RevokeToken.Field


   schema = strawberry.schema(mutation=AuthMutation)

User relay queries
------------------

Currently not supported
~~~~~~~~~~~~~~~~~~~~~~~

excpect to find it here when strawberry will nativly support relay

Example
-------

Handling user accounts becomes super easy.

.. code:: python

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

Check the status of the new user:

.. code:: python

   u = UserModel.objects.last()
   u.status.verified
   # False

During the registration, an email with a verification link was sent.

.. code:: python

   mutation {
     verifyAccount(
       token:"<TOKEN ON EMAIL LINK>",
     ) {
       success,
       errors
     }
   }

Now user is verified.

.. code:: python

   u.status.verified
   # True

Check the `installation
guide <https://strawberry-django-auth.readthedocs.io/en/latest/installation/>`__
or jump to the
`quickstart <https://strawberry-django-auth.readthedocs.io/en/latest/quickstart/>`__.
Or if you prefer, browse the
`api <https://strawberry-django-auth.readthedocs.io/en/latest/api/>`__.

Contributing
------------

See
`CONTRIBUTING.md <https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md>`__

.. |Tests| image:: https://github.com/nrbnlulu/strawberry-django-auth/actions/workflows/tests.yml/badge.svg
.. |Pypi| image:: https://img.shields.io/pypi/v/strawberry-django-auth.svg
   :target: https://pypi.org/project/strawberry-django-auth/
.. |contributions welcome| image:: https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat
   :target: https://github.com/nrbnlulu/strawberry-django-auth/blob/master/CONTRIBUTING.md
.. |Django-graphql-auth| image:: https://github.com/nrbnlulu/django-graphql-auth/
