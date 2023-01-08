import strawberry

from gqlauth.core.types_ import GQLAuthErrors


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
        ...

    schema = strawberry.Schema(query=MainQuery)
    query = """query testAuth($toFail: Boolean!){authEntry(toFail: $toFail){
    ... on GQLAuthError {
      code
      message
    }
    ... on Query {

      a {
        res
      }
    }
  }
}"""
    succeeds = schema.execute_sync(query, variable_values={"toFail": False})
    assert not succeeds.errors
    assert succeeds.data == {"authEntry": {"a": {"res": 2}}}
    fails = schema.execute_sync(query, variable_values={"toFail": True})
    assert not fails.errors
    assert fails.data["authEntry"] == {
        "code": GQLAuthErrors.INVALID_TOKEN.name,
        "message": GQLAuthErrors.INVALID_TOKEN.value,
    }
