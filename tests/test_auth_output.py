import strawberry

from gqlauth.core.constants import Error
from gqlauth.core.types_ import AuthError, AuthWrapper, FieldError


def test_basic_schema():
    @strawberry.type
    class A:
        res: int = 2

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self) -> A:
            return A()

    @strawberry.type
    class MainQuery:
        @strawberry.field
        def auth_entry(self, to_fail: bool = False) -> AuthWrapper[Query]:
            if to_fail:
                return AuthWrapper(
                    success=False,
                    errors=AuthError(
                        field_errors=[FieldError(field="password", code=Error.INVALID_PASSWORD)]
                    ),
                )
            else:
                return AuthWrapper(data=Query(), success=True)

    schema = strawberry.Schema(query=MainQuery)
    query = "query testAuth($toFail: Boolean!){authEntry(toFail: $toFail){data{a{res}}, errors{fieldErrors{field, code, message}}}}"
    succeeds = schema.execute_sync(query, variable_values={"toFail": False})
    assert not succeeds.errors
    assert succeeds.data == {"authEntry": {"data": {"a": {"res": 2}}, "errors": None}}
    fails = schema.execute_sync(query, variable_values={"toFail": True})
    assert not fails.errors
    assert fails.data == {
        "authEntry": {
            "data": None,
            "errors": {
                "fieldErrors": [
                    {
                        "field": "password",
                        "code": Error.INVALID_PASSWORD.name,
                        "message": Error.INVALID_PASSWORD.value,
                    }
                ]
            },
        }
    }
