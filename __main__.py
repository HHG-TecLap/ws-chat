from aiohttp import web
from fileroutes import add_file_routes
from protocol import *
from configparser import ConfigParser
import json, asyncio, atexit
from time import time

config : ConfigParser = ...
CHANNELS : list[tuple[str,str]] = []
CHANNEL_HISTORY : dict[str,list[MessageInfo]] = {}
CONNECTIONS : dict[web.WebSocketResponse,tuple[str,str,set[str]]] = {}

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

        if None in CONNECTIONS[ws] and content["type"] != TYPE_STRS[JoinRegister]:
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

            if name in {name for _, name, _ in CONNECTIONS.values()}:
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

            watched_channels = CONNECTIONS[ws][2]
            if content["state"]:
                watched_channels.add(content["channel"])
                pass
            elif content["channel"] in watched_channels:
                watched_channels.remove(content["channel"])
                pass

            await ws.send_json(ok_message(content["request_id"]))
            pass

        elif content["type"] == TYPE_STRS[ChatMessage]:
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
            author_id = CONNECTIONS[ws][0]
            channel_id = content["channel"]
            date = time()
            
            await ws.send_json(
                confirm_message(content["request_id"],message_id,author_id,channel_id,date)
            )
            await send_many(
                {uws for uws, (uname, uid, watched) in CONNECTIONS.items() if uws is not ws and content["channel"] in watched},
                send_message_server(message_id,user_id,channel_id,date,content["content"])
            )

            CHANNEL_HISTORY.setdefault(content["channel"],[])
            CHANNEL_HISTORY[content["channel"]].append({
                "id":message_id,
                "author":user_id,
                "channel":content["channel"],
                "content":content["content"]
            })
            pass
        
        elif content["type"] == TYPE_STRS[MessageHistoryReq]:
            if not has_keys(content,{"channel"}):
                await ws.send_json(error_message(content["request_id"],ERRORS["MALFORMED_PACKET"],f"The `channel` argument was not supplied. Got {set(content.keys())}"))
                continue
                pass

            if content["channel"] not in {cid for cid, _ in CHANNELS}:
                await ws.send_json(error_message(content["request_id"],ERRORS["UNKNOWN_CHANNEL"],f"Channel with id {content['channel']} does not exist."))
                continue
                pass

            await ws.send_json(message_history_resp(content["request_id"],CHANNEL_HISTORY[content["channel"]]))
            pass
        
        elif content["type"] == TYPE_STRS[AddChannel]:
            if "name" not in content.keys():
                await ws.send_json(error_message(content["request_id"],ERRORS["MALFORMED_PACKET"],f"Malformed packet. Key `name` not included. Got keys {set(content.keys())}"))
                continue
                pass

            if content["name"] in {cname for cid, cname in CHANNELS}:
                await ws.send_json(error_message(content["request_id"],ERRORS["DUPLICATE_CHANNEL"],f"A channel of name {content['name']} already exists"))
                continue
                pass

            cid = generate_snowflake()
            CHANNELS.append((cid,content["name"]))
            
            await ws.send_json(add_channel_resp(content["request_id"],cid))
            await send_all_but(ws,add_channel_notify(cid,content["name"]))
            pass

        elif content["type"] == TYPE_STRS[RemoveChannel]:
            if "id" not in content.keys():
                await ws.send_json(error_message(content["request_id"],ERRORS["MALFORMED_PACKET"],f"Key `id` not passed. Got keys {set(content.keys())}"))
                continue
                pass

            if content["id"] not in {cid for cid, cname in CHANNELS}:
                await ws.send_json(error_message(content["request_id"],ERRORS["UNKNOWN_CHANNEL"],f"Channel of id {content['id']} not found"))
                continue
                pass

            for cdata in CHANNELS:
                if cdata[0] == content["id"]: break
                pass

            CHANNELS.remove(cdata)

            await ws.send_json(ok_message(content["request_id"]))
            await send_all_but(ws,rem_channel_notify(content["id"]))
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

    CONNECTIONS[ws_resp] = (None,None,set())
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
    with open(config["others"]["channels_loc"]) as file:
        channel_names = json.load(file)
        for cname in channel_names:
            cid = generate_snowflake()
            CHANNELS.append((cid,cname))
            CHANNEL_HISTORY[cid] = []
            pass
        pass
    ## Check for formatting
    assert isinstance(CHANNELS,list), RuntimeError(f"{config['others']['channels_loc']} does not contain JSONArray")
    for i, c in enumerate(CHANNELS):
        assert isinstance(c[1],str), f"Malformated channel {i}: {c}"
        pass

    # Auto add routes in remote_files
    add_file_routes(routes,config["net"]["remote_files_loc"],leave_out_top=True)

    # Launch app
    app = web.Application()
    app.add_routes(routes)

    web.run_app(app, host=config["net"]["IP_MASK"],port=config["net"]["PORT"])
    pass

@atexit.register
def exit_save():
    config.write("config.cfg",True)

    with open(config["others"]["channels_loc"],"w") as file:
        json.dump(file, [cname for cid, cname in CHANNELS])
        pass
    pass

if __name__ == "__main__":
    main()