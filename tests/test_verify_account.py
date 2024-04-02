from gqlauth.core.constants import Messages
from gqlauth.core.utils import get_token
from gqlauth.user.signals import user_verified


def _arg_query(token):
    return """
    mutation {
        verifyAccount(token: "%s")
            { success, errors }
        }
    """ % (token)


def test_verify_user(db_unverified_user_status, anonymous_schema):
    user_status = db_unverified_user_status
    user_obj = user_status.user.obj
    assert not user_obj.status.verified
    signal_received = False

    def receive_signal(sender, user, signal):
        assert user.id == user_obj.id
        nonlocal signal_received
        signal_received = True

    user_verified.connect(receive_signal)
    token = get_token(user_obj, "activation")
    executed = anonymous_schema.execute(_arg_query(token)).data["verifyAccount"]
    assert executed["success"]
    assert not executed["errors"]
    assert signal_received
    user_obj.refresh_from_db()
    assert user_obj.status.verified


def test_verified_user(db_verified_user_status, anonymous_schema):
    user_status = db_verified_user_status
    user_obj = user_status.user.obj
    token = get_token(user_obj, "activation")
    executed = anonymous_schema.execute(_arg_query(token)).data["verifyAccount"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.ALREADY_VERIFIED


def test_invalid_token(anonymous_schema):
    executed = anonymous_schema.execute(_arg_query("fake token")).data["verifyAccount"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.INVALID_TOKEN


def test_other_token(db_unverified_user_status, anonymous_schema):
    user_status = db_unverified_user_status
    user_obj = user_status.user.obj
    token = get_token(user_obj, "password_reset")
    executed = anonymous_schema.execute(_arg_query(token)).data["verifyAccount"]
    assert not executed["success"]
    assert executed["errors"]["nonFieldErrors"] == Messages.INVALID_TOKEN
