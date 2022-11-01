from sanic import Sanic
from sanic.response import json, HTTPResponse
from sanic.request import Request

from authentication import signup, activate, login, logout

from Crypto.Hash import SHA1

from models import Commodity, Account, Transaction, ApiUser
from serializers import AUSerializer, CommSerializer, AccSerializer, TransSerializer
from configparser import ConfigParser

c = ConfigParser()
c.read("../app.conf")
ssecret=c["PAYMENT"]["secret"]

app = Sanic.get_app("main")

async def verify_tx(signature, transaction_id, user_id, account_id, amount):
    s = SHA1.new()
    s.update(f"{ssecret}:{transaction_id}:{user_id}:{account_id}:{amount}".encode())
    my_hash = s.hexdigest()
    if my_hash == signature:
        tx = Transaction(value = amount, tx_id = transaction_id, account_from_id = account_id)
        await tx.save()
        acc = await Account.get_or_none(id = account_id)
        acc.balance = acc.balance + amount
        await acc.save()
        return (acc, tx)
    else:
        return (None, None)


def auth_not_needed(f):
    async def wrapper(*args, **kwargs):
        if args[0].ctx.is_authenticated:
            return json({"error": "already authenticated"}, status = 400)
        return await f(*args, **kwargs)
    return wrapper

def auth_needed(f):
    async def wrapper(*args, **kwargs):
        if not args[0].ctx.is_authenticated:
            return json({"error": "need authentication"}, status = 401)
        return await f(*args, **kwargs)
    return wrapper

def admin_only(f):
    async def wrapper(*args, **kwargs):
        if not args[0].ctx.user.is_admin:
            return json({"error": "administratorship required"}, status = 401)
        return await f(*args, **kwargs)
    return wrapper

async def authing(auth_method, request):
    if request.json:
        status, user_json = await auth_method(request = request, **request.json)
    else:
        status, user_json = await auth_method(request = request)
    return json(user_json, status = status)

@app.route("/auth/signup", methods = ["POST"])
@auth_not_needed
async def signup_handler(request: Request) -> HTTPResponse:
    return await authing(signup, request)

@app.route("/auth/signup/<signup_link:str>")
@auth_not_needed
async def activate_handler(request: Request, signup_link: str) -> HTTPResponse:
    request.ctx.signup_link = signup_link
    return await authing(activate, request)

@app.route("/auth/login", methods = ["POST"])
@auth_not_needed
async def login_handler(request: Request) -> HTTPResponse:
    return await authing(login, request)


@app.route("/auth/logout", methods = ["POST"])
@auth_needed
async def logout_handler(request: Request) -> HTTPResponse:
    return await authing(logout, request)


@app.route("/shop")
async def shop_list(request: Request) -> HTTPResponse:
    catalogue = await Commodity.all()
    res = []
    for piece in catalogue:
        res.append({"id": piece.id, "title": piece.title, "description": piece.description, "price": piece.price})
    return json(res)

@app.route("/shop/<item_id:int>/buy", methods = ["POST"])
@auth_needed
async def buy_item(request: Request) -> HTTPResponse:
    item = await Commodity.get_or_none(id=id)
    account = await Account.get_or_none(id = request.json.get("account_id", 0))
    if item == None or account == None:
        return json({"error": "either item or account does not exist"}, status=404)
    if account.balance >= item.price:
        account.balance = account.balance - item.price
        return json({"account": {"id": account.id, "balance": account.balance}, "item": {"id": item.id, "title": item.title, "description": item.description, "price": item.price}})
    return json({"error": "insufficient balance"}, status = 400)

@app.route("/accounts")
@auth_needed
async def get_all_accs(request: Request) -> HTTPResponse:
    accs = await Account.filter(owner = request.ctx.user)
    accser = AccSerializer()
    await accser.s(accs)
    return json(accser.data)

@app.route("/accounts/create", methods = ["POST"])
@auth_needed
async def create_acc(request: Request) -> HTTPResponse:
    acc = Account(owner = request.ctx.user)
    await acc.save()
    return json({"id": acc.id, "balance": acc.balance})

@app.route("/payment/transfer", methods = ["POST"])
async def pay_money(request: Request) -> HTTPResponse:
    acc, tx = await verify_tx(**request.json)
    if tx != None and acc != None:
        return json({'account': {'id': acc.id, 'balance': acc.balance, 'owner_id': acc.owner.id}, 'transaction': {'id': tx.id, 'tx_id': tx.tx_id, 'account': tx.account_from.id, 'timestamp': tx.timestamp}})
    else:
        return json({'error': 'bad request'}, status = 400)

@app.route("/accounts/history")
@auth_needed
async def tx_history(request: Request) -> HTTPResponse:
    accs = await request.ctx.user.accounts
    tx_h = []
    for acc in accs:
        for tx in await acc.transaction_history:
            tx_h.append(tx)
    res = [{"id" : tx.id, "account": tx.account_from, "timestamp": tx.timestamp} for tx in tx_h]
    return json(TransSerializer(tx_h).data)

@app.route("/admin/commodities")
@admin_only
async def admin_comms(request: Request) -> HTTPResponse:
    c = await Commodity.all()
    return CommSerializer(c).data

@app.route("/admin/commodities/new", methods = ["POST", ])
@admin_only
async def admin_new_commodities(request: Request) -> HTTPResponse:
    comms = request.json.get("comms", None)
    res = []
    if comms:
        for comm in comms:
            try:
                c, created = await Commodity.get_or_create(**comm)
                if created:
                    await c.save()
                    res.append(comm)
            except Exception as e:
                pass
        return json({"created": res})
    else:
        return json({"error" : "provide commodities to create"}, status = 400)

@app.route("/admin/users")
@admin_only
async def admin_users(request: Request) -> HTTPResponse:
    u = await ApiUser.all()
    a = AUSerializer()
    a.accounts_serializer = AccSerializer(fields = ("id", "balance", "transaction_history"))
    await a.s(u)
    return json(a.data)

@app.route("/admin/users/disable", methods = ["POST", ])
@admin_only
async def admin_accounts_disable(request: Request) -> HTTPResponse:
    if request.json.get("user_ids", None):
        users = await ApiUser.filter(id__in == request.json["user_ids"])
        for u in users:
            u.is_active = False
            await u.save()
        return json(requset.json["user_ids"])
    else:
        return json({"error": "proide user_ids list of user ids to disable"}, status = 400)

@app.route("/admin/accounts")
@admin_only
async def admin_accounts(request: Request) -> HTTPResponse:
    accs = await Account.all()
    a = AccSerializer()
    await a.s(accs)
    return json(a.data)


@app.route("/admin/accounts/<acc_id:int>")
@admin_only
async def admin_accounts(request: Request, acc_id: int) -> HTTPResponse:
    acc = await Account.get_or_none(id = acc_id)
    if acc:
        a = AccSerializer(transaction_history_serializer = TransSerializer())
        await a.s(acc, many = False)
        return json(a.data)
    else:
        return json({"error": "not found"}, status = 404)

