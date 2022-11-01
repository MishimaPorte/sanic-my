from models import ApiUser, Commodity, Account, Transaction

from Crypto.Hash import SHA1
from Crypto.Random import get_random_bytes

from tortoise.exceptions import IntegrityError
import jwt

from cryptography.hazmat.primitives import serialization

from datetime import datetime

with open("../keys/id_rsa", "r") as first_keyfile:
    private_key = serialization.load_ssh_private_key(
        first_keyfile.read().encode(), password=b""
    )

with open("../keys/id_rsa.pub", "r") as second_keyfile:
    public_key = serialization.load_ssh_public_key(second_keyfile.read().encode())


async def generate_jwt(user):
    header = {"typ": "JWT", "alg": "RS256", "iat": datetime.now().isoformat()}
    payload = {
        "user": user.login,
    }
    token = jwt.encode(payload=payload, key=private_key, algorithm="RS256")
    user.private_token = token
    await user.save()
    return token


def hash(password: str, salt: str):
    h = SHA1.new()
    h.update(f"{password}:{salt}".encode())
    return h.hexdigest()


def salt():
    return get_random_bytes(5).hex()


def create_signup_token(login: str):
    h = SHA1.new()
    h.update(f"{login}:{salt()}".encode())
    return h.hexdigest()[:20]


async def signup(request, login: str = None, password: str = None):
    if login == None or password == None:
        return (400, {"error": "bad credentials"})
    user_salt = salt()
    try:
        user, created = await ApiUser.get_or_create(
            login=login, password=hash(password, user_salt), salt=user_salt
        )
    except Exception as e:
        return (409, {"error": e.__str__()})
    if created:
        user.activate_token = create_signup_token(login)
        await user.save()
        return (200, {"activation_link": f"/auth/signup/{user.activate_token}"})
    else:
        return (200, {"activation_link": f"/auth/signup/{user.activate_token}"})


async def activate(request):
    link = request.ctx.signup_link
    user = await ApiUser.get_or_none(activate_token=link)
    if not user == None:
        if user.is_active:
            return (200, {"login": user.login})
        user.is_active = True
        await user.save()
        return (200, {"login": user.login})
    else:
        return (404, {"error": "No such user activation link exists."})


async def login(login: str, password: str, request):
    user = await ApiUser.get_or_none(login=login)
    if not user == None:
        if not user.is_active:
            return (401, {"error": "activate account first"})
        salted_password = hash(password, user.salt)
        if salted_password == user.password:
            return (200, {"jwt": await generate_jwt(user)})
        else:
            return (401, {"error": "Incorrect password"})
    else:
        return (
            404,
            {"error": "Trying to log as a user that does not, technically, exist."},
        )


async def logout(request):
    request.ctx.user.private_token = None
    await request.ctx.user.save()
    return (200, {})
