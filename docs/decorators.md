
# Decorators

---

    <a id="decorators.wraps"></a>

## wraps

<a id="decorators.g_user"></a>

## g\_user

<a id="decorators.Messages"></a>

## Messages

<a id="decorators.WrongUsage"></a>

## WrongUsage

<a id="decorators.PermissionDenied"></a>

## PermissionDenied

<a id="decorators.login_required"></a>

#### login\_required

```python
def login_required(fn)
```

If the user is registered

<a id="decorators.verification_required"></a>

#### verification\_required

```python
def verification_required(fn)
```

if the user was approved

<a id="decorators.secondary_email_required"></a>

#### secondary\_email\_required

```python
def secondary_email_required(fn)
```

<a id="decorators.password_confirmation_required"></a>

#### password\_confirmation\_required

```python
def password_confirmation_required(fn)
```

<a id="decorators.allowed_permissions"></a>

#### allowed\_permissions

```python
def allowed_permissions(roles: list)
```

checks a list of roles if it applies to a user
verification required by default.

