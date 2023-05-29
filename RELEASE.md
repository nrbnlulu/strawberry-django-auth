Release type: patch

This release fixes the way we call django's `send_mail()` previously
we were passing the `DjangoSetting` object directly, but now we pass its value.

fixes #387
