from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise import fields
from tortoise.fields.relational import ReverseRelation
from models import ApiUser, Commodity, Account, Transaction


class Serializer:
    fields: str = None
    model: Model

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        if self.fields == None:
            self.fields = self.model._meta.fields
            for field in self.fields:
                if f"{field}_id" in self.fields:
                    self.fields.pop(f"{field}_id")

    async def s(self, qs, fields=None, many=True):
        if fields == None:
            fields = self.fields or self.model._meta.fields
        if not many:
            qs = [
                qs,
            ]
        res = []
        for item in qs:
            d = {}
            for field in fields:
                val = item.__getattribute__(field)
                if issubclass(type(val), QuerySet):
                    val = await val
                    if hasattr(
                        self, f"{field}_serializer"
                    ):  # self.__hasattr__(f"{field}_serializer"):
                        await self.__getattribute__(f"{field}_serializer").s(
                            val, many=False
                        )
                        d.update(
                            {field: self.__getattribute__(f"{field}_serializer").data}
                        )
                    else:
                        d.update({field: val.id})
                elif issubclass(type(val), ReverseRelation):
                    val = await val
                    if hasattr(self, f"{field}_serializer"):
                        await self.__getattribute__(f"{field}_serializer").s(val)
                        d.update(
                            {field: self.__getattribute__(f"{field}_serializer").data}
                        )
                    else:
                        d2 = []
                        for i in val:
                            d2.append({"id": i.id})
                        d.update({field: d2})
                else:
                    d.update({field: val})
            res.append(d)
        if many:
            self.data = res
        else:
            self.data = res[0]


class AUSerializer(Serializer):
    model = ApiUser


class CommSerializer(Serializer):
    model = Commodity


class AccSerializer(Serializer):
    model = Account
    fields = ("id", "owner_id", "balance", "transaction_history")


class TransSerializer(Serializer):
    model = Transaction
    fields = ("id", "tx-id", "value", "account_from", "timestamp")
