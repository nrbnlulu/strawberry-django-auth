import strawberry
from gqlauth.models import Captcha
from gqlauth.types import CaptchaType
from gqlauth.user.mutations import UserMutations
from gqlauth.user.queries import UserQueries
from strawberry.tools import merge_types

@strawberry.type
class CaptchaMutation:
    @strawberry.mutation
    def captcha(self, info) -> CaptchaType:
        return Captcha.create_captcha()


AuthQueries = merge_types('Auth', (UserQueries,))
AuthMutations = merge_types('AuthMutations', (CaptchaMutation, UserMutations))

