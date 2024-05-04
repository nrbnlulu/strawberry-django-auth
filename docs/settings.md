
> auto generated using `pydoc_markdown`
___
## GqlAuthSettings

```python
@dataclass
class GqlAuthSettings()
```

### ALLOW\_LOGIN\_NOT\_VERIFIED

>

### LOGIN\_FIELDS

> These fields would be used to authenticate with SD-jwt `authenticate`
> function. This function will call each of our `AUTHENTICATION_BACKENDS`,
> And will return the user from one of them unless `PermissionDenied` was
> raised. You can pass any fields that would be accepted by your backends.
>
> **Note that `password field` is mandatory and cannot be removed.**

### LOGIN\_REQUIRE\_CAPTCHA

> Whether login will require captcha verification.

### REGISTER\_MUTATION\_FIELDS

> Fields on register, plus password1 and password2, can be a dict like
> UPDATE_MUTATION_fieldS setting.

### REGISTER\_REQUIRE\_CAPTCHA

> Whether register will require captcha verification.

### CAPTCHA\_EXPIRATION\_DELTA

> captcha stuff
> captcha expiration delta.

### CAPTCHA\_MAX\_RETRIES

> max number of attempts for one captcha.

### CAPTCHA\_TEXT\_FACTORY

> A callable with no arguments that returns a string.
>
> This will be used to generate the captcha image.

### CAPTCHA\_TEXT\_VALIDATOR

> A callable that will receive the original string vs user input and
> returns a boolean.

### FORCE\_SHOW\_CAPTCHA

> Whether to show the captcha image after it has been created for
> debugging purposes.

### CAPTCHA\_SAVE\_IMAGE

> If True, an png representation of the captcha will be saved under
> MEDIA_ROOT/captcha/<datetime>/<uuid>.png.

### UPDATE\_MUTATION\_FIELDS

> Fields on update account mutation.

### ALLOW\_DELETE\_ACCOUNT

> If True, DeleteAcount mutation will permanently delete the user.

### ALLOW\_PASSWORDLESS\_REGISTRATION

> Whether to allow registration with no password.

### JWT\_SECRET\_KEY

> Key used to sign the JWT token.

### JWT\_ALGORITHM

> Algorithm used for signing the token.

### JWT\_TIME\_FORMAT

> A valid 'strftime' string that will be used to encode the token
> payload.

### JWT\_PAYLOAD\_HANDLER

> A custom function to generate the token datatype, its up to you to
> encode the token.

### JWT\_PAYLOAD\_PK

> Field that will be used to generate the token from a user instance and
> retrieve user based on the decoded token. The default value is the username
> field of the User model. If you want to change it to id, for example, you
> can use the id_field defined in gqlauth.settings_type and change it like
> JWT_PAYLOAD_PK=id_field.
>
> *This filed must be unique in the database*

### JWT\_TOKEN\_FINDER

> A hook called by `GqlAuthRootField` to find the token. Accepts the
> request object (might be channels scope dict or django request object)
>
> **remember to strip the "JWT " prefix if you override this.**

### JWT\_EXPIRATION\_DELTA

> Timedelta added to `utcnow()` to set the expiration time.
>
> When this ends you will have to create a new token by logging in or
> using the refresh token.

### JWT\_LONG\_RUNNING\_REFRESH\_TOKEN

> Whether to enable refresh tokens to be used as an alternative to login
> every time the token is expired.

### JWT\_REFRESH\_TOKEN\_N\_BYTES

> Number of bytes for long running refresh token.

### JWT\_REFRESH\_EXPIRATION\_DELTA

> Refresh token expiration time delta.
