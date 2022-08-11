
> auto generated using `pydoc_markdown`
___
## wraps

## Info

## g\_info

## g\_user

## MutationNormalOutput

## Messages

## PermissionDenied

## login\_required

```python
def login_required(fn)
```

> If the user is registered

## verification\_required

```python
def verification_required(fn)
```

> if the user was approved

## secondary\_email\_required

```python
def secondary_email_required(fn)
```

## \_password\_confirmation\_required

```python
def _password_confirmation_required(fn)
```

> not to be used publicly.

## allowed\_permissions

```python
def allowed_permissions(roles: list)
```

> checks a list of roles if it applies to a user
> verification required by default.
