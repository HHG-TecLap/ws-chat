from aiohttp import web
from fileroutes import add_file_routes
from protocol import *
from configparser import ConfigParser
import json, asyncio

config : ConfigParser = ...
CHANNELS : list[tuple[int,str]] = []
CHANNEL_HISTORY : dict[int,list[MessageInfo]] = {}
CONNECTIONS : dict[web.WebSocketResponse,tuple[int,str,dict[int,bool]]] = {}

routes = web.RouteTableDef()

has_keys = lambda dict, keys: set(dict.keys()).issuperset(keys)

async def send_many(targets : set[web.WebSocketResponse], message : Message):
    await asyncio.gather(*{t.send_json(message) for t in targets})
    pass

async def send_all(message : Message):
    await send_many(CONNECTIONS.keys(),message)
    pass

async def send_all_but(exception : web.WebSocketResponse, message : Message):
    targets = set(CONNECTIONS.keys()).copy()
    targets.remove(exception)
    await send_many(targets,message)
    pass

async def ws_handler(ws : web.WebSocketResponse):
    user_id = ...
    name = ...

    async for msg in ws:
        content : Message = msg.json()

        if not has_keys(content,{"type","request_id"}):
            await ws.send_json(error_message(
                content.get("request_id"), 
                ERRORS["MALFORMED_PACKET"],
                f"base structure of packet not included. Found keys {set(content.keys())}"
            ))
            continue
            pass

        if CONNECTIONS[ws][:2] == (None,None) and content["type"] != TYPE_STRS[JoinRegister]:
            await ws.send_json(error_message(content["request_id"], ERRORS["NO_LOGIN"],"client not logged in but sending messages already"))
            continue
            pass

        if content["type"] == TYPE_STRS[JoinRegister]:
            if None not in CONNECTIONS[ws]:
                await ws.send_json(error_message(content["request_id"], ERRORS["DUPLICATE_LOGIN"], "client already logged in but sent login"))
                continue
                pass

            name = content.get("name")
            if name is None:
                await ws.send_json(error_message(content["request_id"], ERRORS["MALFORMED_PACKET"], "argument `name` not passed"))
                continue
                pass

            if name in {name for _, name in CONNECTIONS.values()}:
                await ws.send_json(error_message(content["request_id"], ERRORS["DUPLICATE_NAME"], f"A user with name {name} not passed"))
                continue
                pass

            user_id = generate_snowflake()
            CONNECTIONS[ws] = (user_id, name, set())

            await ws.send_json(join_message(content["request_id"],user_id,name))
            await send_all_but(ws,join_message(None,user_id,name))
            pass
        
        elif content["type"] == TYPE_STRS[Heartbeat]:
            await ws.send_json(heartbeat_ack(content["request_id"]))
            pass

        elif content["type"] == TYPE_STRS[ChannelListReq]:
            await ws.send_json(channel_list_resp(content["request_id"], CHANNELS))
            pass

        elif content["type"] == TYPE_STRS[UserListReq]:
            await ws.send_json(user_list_resp(
                content["request_id"],
                [(uid, uname) for uid, uname, _ in CONNECTIONS.values()]
            ))
            pass

        elif content["type"] == TYPE_STRS[SetChannelSubscription]:
            if not has_keys(content,{"channel","state"}):
                await ws.send_json(error_message(
                    content["request_id"],
                    ERRORS["MALFORMED_PACKET"],
                    f"`channel` or `state` not passed. Got {set(content.keys())}"
                ))
                continue
                pass

            if content["channel"] not in {c[0] for c in CHANNELS}:
                await ws.send_json(error_message(
                    content["request_id"],
                    ERRORS["UNKNOWN_CHANNEL"],
                    f"channel id {content['channel']} not found"
                ))
                continue
                pass

            CONNECTIONS[ws][2][content["channel"]] = content["state"]
            await ws.send_json(ok_message(content["request_id"]))
            pass

        elif content["type"] == TYPE_STRS[ChatMessage]:
            content : ChatMessage
            if not has_keys(content,{"author","channel","content","id"}):
                await ws.send_json(error_message(
                    content["request_id"],
                    ERRORS["MALFORMED_PACKET"],
                    f"`author`, `channel`, `content`, or `id` not passed. Got {set(content.keys())}"
                ))
                continue
                pass
            if content["channel"] not in {c[0] for c in CHANNELS}:
                await ws.send_json(error_message(
                    content["request_id"],
                    ERRORS["UNKNOWN_CHANNEL"],
                    f"channel id {content['channel']} not found"
                ))
                continue
                pass

            message_id = generate_snowflake()
            
            await ws.send_json(
                confirm_message(content["request_id"],message_id)
            )
            await send_many(
                {uws for uws, (uname, uid, watched) in CONNECTIONS.items() if uws is not ws and watched.get(content["channel"],False)},
                send_message_server(message_id,user_id,content["channel"],content["content"])
            )

            CHANNEL_HISTORY.setdefault(content["channel"],[])
            CHANNEL_HISTORY[content["channel"]].append({
                "id":message_id,
                "author":user_id,
                "channel":content["channel"],
                "content":content["content"]
            })
            pass
        pass

    CONNECTIONS.pop(ws)
    if user_id is not ...:
        await send_all(leave_message(None,user_id))
        pass
    pass

@routes.get("/ws")
async def websocket_request(request : web.BaseRequest):
    ws_resp = web.WebSocketResponse()
    await ws_resp.prepare(request)

    CONNECTIONS[ws_resp] = (None,None)
    await ws_handler(ws_resp)

    return ws_resp
    pass

@routes.get("/")
async def main_page(request):
    raise web.HTTPFound("/index.html")
    pass

def main():
    global config
    config = ConfigParser()
    config.read("config.cfg")

    # Load in channels
    global CHANNELS
    with open(config["others"]["channels_loc"]) as file:
        CHANNELS = json.load(file)
        pass
    ## Check for formatting
    assert isinstance(CHANNELS,list), RuntimeError(f"{config['others']['channels_loc']} does not contain JSONArray")
    for i, c in enumerate(CHANNELS):
        assert isinstance(c,list) and len(c)==2 and isinstance(c[0],int) and isinstance(c[1],str), f"Malformated channel {i}: {c}"
        pass

    # Auto add routes in remote_files
    add_file_routes(routes,config["net"]["remote_files_loc"],leave_out_top=True)

    # Launch app
    app = web.Application()
    app.add_routes(routes)

    web.run_app(app, host=config["net"]["IP_MASK"],port=config["net"]["PORT"])
    pass

if __name__ == "__main__":
    main()