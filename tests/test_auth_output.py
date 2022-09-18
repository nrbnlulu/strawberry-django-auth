import strawberry

from gqlauth.core.types_ import AuthOutput, ErrorMessage, GqlAuthError


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
        def auth_entry(self, to_fail: bool = False) -> AuthOutput[Query]:
            if to_fail:
                return AuthOutput(error=ErrorMessage(code=GqlAuthError.INVALID_TOKEN))
            else:
                return AuthOutput(node=Query(), success=True)

    schema = strawberry.Schema(query=MainQuery)
    query = "query testAuth($toFail: Boolean!){authEntry(toFail: $toFail){node{a{res}}, error{code, message}}}"
    succeeds = schema.execute_sync(query, variable_values={"toFail": False})
    assert not succeeds.errors
    assert succeeds.data == {"authEntry": {"error": None, "node": {"a": {"res": 2}}}}
    fails = schema.execute_sync(query, variable_values={"toFail": True})
    assert not fails.errors
    assert fails.data == {
        "authEntry": {
            "node": None,
            "error": {
                "code": GqlAuthError.INVALID_TOKEN.name,
                "message": GqlAuthError.INVALID_TOKEN.value,
            },
        }
    }
