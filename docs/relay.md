# Relay

---

Import mutations from the ``relay`` module:

```python

from gqlauth.user import relay

@strawberry.type
class AuthMutation:
   register = relay.Register.Field
```
___

#### Note that relay is not supported for queries yet.
