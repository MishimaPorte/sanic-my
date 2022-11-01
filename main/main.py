from sanic import Sanic

from tortoise import Tortoise, run_async
from configparser import ConfigParser

config = ConfigParser()
config.read("../app.conf")
pg_conf = config["POSTGRES"]

TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{pg_conf['user']}:{pg_conf['password']}@{pg_conf['host']}:{pg_conf['port']}/{pg_conf['db']}"
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}


async def initdb():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


app = Sanic(name="main")

import endpoints
import middleware
import ex

if __name__ == "__main__":
    run_async(initdb())
    app.run(host = "0.0.0.0")
