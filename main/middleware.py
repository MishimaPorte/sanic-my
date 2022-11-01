from sanic import Sanic

from models import ApiUser

from cryptography.hazmat.primitives import serialization
import jwt

app = Sanic.get_app("main")

with open("../keys/id_rsa.pub", "r") as keyfile:
    pkey = serialization.load_ssh_public_key(keyfile.read().encode())


class AnonymousUser:
    login = "anon"
    password = None
    salt = None
    activate_token = None
    private_token = None
    is_active = False
    is_admin = False


@app.middleware("request")
async def auth(request):
    if request.token != None:
        user_token = jwt.decode(request.token, key=pkey, algorithms="RS256")
        login = user_token.get("user", None)
        if login:
            user = await ApiUser.get_or_none(login=login)
            if user:
                if user.private_token == request.token:
                    request.ctx.user = user
                    request.ctx.is_authenticated = True
                    return
    request.ctx.user = AnonymousUser()
    request.ctx.is_authenticated = False
