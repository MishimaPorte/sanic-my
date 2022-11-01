from tortoise.models import Model
from tortoise import fields


class ApiUser(Model):
    login = fields.CharField(max_length=30, unique=True)
    password = fields.CharField(max_length=64)
    salt = fields.CharField(max_length=10)
    activate_token = fields.CharField(max_length=20, null=True)
    private_token = fields.CharField(max_length=660, null=True)
    is_active = fields.BooleanField(default=False)
    is_admin = fields.BooleanField(default=False)


class Commodity(Model):
    title = fields.CharField(max_length=30)
    description = fields.TextField()
    price = fields.BigIntField()


class Account(Model):
    balance = fields.BigIntField(default=0)
    owner = fields.ForeignKeyField("models.ApiUser", related_name="accounts")


class Transaction(Model):
    value = fields.BigIntField()
    tx_id = fields.BigIntField()
    account_from = fields.ForeignKeyField(
        "models.Account", related_name="transaction_history"
    )
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        unique_together = (("account_from", "tx_id"),)
