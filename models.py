from __future__ import annotations

from tortoise.models import Model
from tortoise.fields import BigIntField, BooleanField, TextField

class Configuration(Model):
    guild = BigIntField(True, unique=True, null=False)
    enabled = BooleanField(default=True)
    message = TextField(null=False, default="¡Gracias por contactar con el soporte! En breves le atenderemos...")
    channel = BigIntField(null=True, default=None)
    support_role = BigIntField(null=True, default=None)
