# Captcha

---
this package provides a fully functional captcha validation system
the default setting are:

```py
    LOGIN_REQUIRE_CAPTCHA = True,
    REGISTER_REQUIRE_CAPTCHA = True,
```
if you don't like this set them to False.

The Captcha is available to query via a base64 encoded string or via a static .png image.

!!! Note "Note: The Image is in PNG format"

=== "base64"

    ```graphql
    mutation MyMutation {
      captcha {
        uuid
        pilImage
      }
    }
    ```

    !!! Note "You will further be needed to implement a translation in the UI."


=== "static"
    For the creation of a static set `CAPTCHA_SAVE_IMAGE = True` on your settings.
    This will use django's Imagefield to store the captcha image.
    You will also be needed to include a path in your urlpatterns for development,
    [as per the documentation](https://docs.djangoproject.com/en/4.0/howto/static-files/#serving-files-uploaded-by-a-user-during-development).

    ```graphql
    mutation MyMutation {
      captcha {
        uuid
        image{
          width
          height
          url

        }
      }
    }
    ```
