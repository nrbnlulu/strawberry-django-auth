Release type: minor

This release updates to the latest version of strawberry
and removes dependencies with strawberry-django-plus.

- The directive `IsVerified` is migrated to the new field
extensions API and extends the django base permission
extension.

- The Channels middleware will inject the user in `request.user`
or `request.scope["UserOrError"]`
