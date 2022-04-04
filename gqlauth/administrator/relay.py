import logging
from gqlauth.bases.mixins import DynamicRelayMutationMixin, DynamicInputMixin
from gqlauth.administrator.mixins import VerifyUserMixin

logging.getLogger(name=__name__)



class VerifyUser(DynamicRelayMutationMixin, DynamicInputMixin, VerifyUserMixin):
    ...
