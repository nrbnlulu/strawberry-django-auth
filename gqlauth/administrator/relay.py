import logging

from gqlauth.administrator.mixins import VerifyUserMixin
from gqlauth.bases.mixins import DynamicInputMixin, DynamicRelayMutationMixin

logging.getLogger(name=__name__)


class VerifyUser(DynamicRelayMutationMixin, DynamicInputMixin, VerifyUserMixin):
    ...
