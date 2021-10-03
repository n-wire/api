from sanic import Sanic
from sanic.response import json, text, html, file
from sanic_cors import CORS, cross_origin
from auth import protected, login
import string
import random
from admin import Admin
from pymongo.errors import DuplicateKeyError
import asyncio
from nodewire import Message
import os
import aiofiles

CP = os.environ['CP']


app = Sanic("NodeWire")
CORS(app, supports_credentials=True)

app.config.SECRET = "this is my secret"
app.blueprint(login)
app.ctx.db = Admin()
app.static('/', './frontend')

@app.listener("before_server_start")
async def setup(app, loop):
    try:
        print('NodeWire Rest Server started')
    except:
        pass
    

@app.route('/')
async def home(request):
    return await file('./frontend/index.html')

@app.route("/node/<nodename:string>/<port:string>", methods=['GET', 'POST', 'OPTIONS'])
@protected
async def node_get_post(request, nodename:str, port:str):
    if request.method == 'GET':
        reader, writer = await asyncio.open_connection(CP, 9001)
        writer.write(f'{request.ctx.instance}:{nodename} get {port} {request.ctx.user}\n'.encode())
        await writer.drain()
        try:
            raw = (await asyncio.wait_for(reader.readline(), timeout=1.0)).decode('utf8')
            if raw:
                val = Message(raw)
            else:
                val = None
        except asyncio.TimeoutError:
            val = None
        writer.close()
        if val is None: return json(None)
        return json(val.value)
    elif request.method == 'POST':
        reader, writer = await asyncio.open_connection(CP, 9001)
        writer.write(f'{request.ctx.instance}:{nodename} set {port} {request.json} {request.ctx.user}\n'.encode())
        await writer.drain()
        writer.close()
        return text('success')


def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route("/createUser", methods=['POST', 'OPTIONS'])
async def create_user(request):
    print(request.json)
    if 'name' in request.json and 'email' in request.json and 'password' in request.json:
        try:
            app.ctx.db.create_instance(id_generator(), {'fullname': request.json["name"], 'email': request.json["email"], 'password': request.json["password"]})
        except DuplicateKeyError:
            return text('user exists already')

        return text('success')
    else:
        return text('failed')

@app.route('/add_gateway', methods=['POST', 'OPTIONS'])
@protected
async def add_gateway(request):
    result = app.ctx.db.add_gateway(request.ctx.user, request.json['gateway'])
    if result == True:
        return text('success')
    else:
        return text(result)

@app.route('/del_gateway', methods=['POST', 'OPTIONS'])
@protected
async def del_gateway(request):
    user = request.json
    if app.ctx.db.del_gateway(request.ctx.user, user['gateway']):
        return text('success')
    else:
        return text('failed')

@app.route('/register', methods=['POST', 'OPTIONS'])
@protected
async def register(request):
    reader, writer = await asyncio.open_connection(CP, 9001)
    writer.write(f'{request.ctx.instance}:cp set id {request.json["nodename"]} {request.json["id"]} {request.json["newname"]} {request.ctx.user}\n'.encode())
    writer.write(f'{request.ctx.instance}:cp register {request.json["newname"]} {request.json["id"]} {request.ctx.user}\n'.encode())
    await writer.drain()
    try:
        await asyncio.wait_for(reader.readline(), timeout=1.0)
    except asyncio.TimeoutError:
        pass
    writer.close()
    return text('success')


@app.route('/create_app', methods=['POST', 'OPTIONS'])
@protected
async def create_app(request):
    try:
        return json(app.ctx.db.create_app(request.ctx.user, request.json["appname"]))
    except Exception as ex:
        return text(str(ex))

@app.route('/open_app', methods=['POST', 'OPTIONS'])
@protected
async def open_app(request):
    try:
        return json(app.ctx.db.open_app(request.ctx.user, request.json["appname"]))
    except Exception as ex:
        return text(str(ex))


@app.route('/save_app', methods=['POST', 'OPTIONS'])
@protected
async def save_app(request):
    try:
        json(app.ctx.db.save_app(request.ctx.user, request.json["app"]))
        return text('success')
    except Exception as ex:
        return text(str(ex))

@app.route("/upload", methods=['POST'])
@protected
async def upload(request):
    if not os.path.exists('./storage/'+request.ctx.instance):
        os.makedirs('./storage/'+request.ctx.instance)
    print('file', request.files)
    async with aiofiles.open('./storage/'+request.ctx.instance+"/"+request.files["file"][0].name, 'wb') as f:
        await f.write(request.files["file"][0].body)
    f.close()

    return text('success')

@app.route('/storage/<filename:string>')
@protected
async def storage(request, filename:str):
    return await file('./storage/'+request.ctx.instance+"/"+filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, access_log=True)