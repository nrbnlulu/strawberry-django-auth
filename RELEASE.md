Release type: patch

Fix issue: TokenType.is_expired() fails since it's comparing naive timestamp with aware timestamp
Replace payload.exp with payload.exp.replace(tzinfo=timezone.utc) when it is compared with utc_now()
