from base64 import b64decode, b64encode
import typing

from PIL.Image import Image
import strawberry

image = strawberry.scalar(
    typing.NewType("image", Image),
    serialize=lambda v: b64encode(v).decode("ascii"),
    parse_value=lambda v: b64decode(v),
)
