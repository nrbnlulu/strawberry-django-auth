Release type: patch

This release fixes the way we set the refresh token's field `revoked`.
Previously we were passing a naive DateTime object but now we pass the timestamp with the timezone info.

fixes #395
