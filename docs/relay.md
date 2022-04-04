# Relay

---

Import mutations from the ``relay`` module:

```python

from gqlauth.user import relay

class AuthMutation(graphene.ObjectType):
   register = relay.Register.Field
```
