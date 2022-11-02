from sanic import Sanic
from sanic.response import text

app = Sanic.get_app("main")

#@app.exception(Exception)
#async def catch_anything(request, exception):
#    return text("Server error", status=500)
