# Relay

---

Import mutations from the ``relay`` module:

```python
import strawberry
from gqlauth.user import relay

@strawberry.type
class AuthMutation:
   register = relay.Register.field
```
___

#### Note that relay is not supported for queries yet.
