ERRORS = {
    "MALFORMED_PACKET":0b00000000000000000000000000000000,
    "NO_PERMISSION":0b00000000000000000000000000000001,
    "NO_LOGIN":0b00000000000000000000000000010000,
    "DUPLICATE_NAME":0b00000000000000000000000000010001,
    "DUPLICATE_LOGIN":0b00000000000000000000000000010010,
    "UNKNOWN_CHANNEL":0b00000000000000000000000000100000,
    "DUPLICATE_CHANNEL":0b00000000000000000000000000100001,
}

from typing import TypedDict

class JoinInfo(TypedDict):
    id: str
    name: str
    pass

class MessageInfo(TypedDict):
    id: str
    author: str
    channel: str
    content: str|None
    date: float
    pass

class Message(TypedDict):
    request_id: int
    type: str
    pass

class ConfirmResp(Message):
    pass

class ErrorResp(Message):
    code: int
    message: str
    pass

class JoinMessage(Message):
    data: JoinInfo
    pass

class LeaveMessage(Message):
    user: str
    pass

class UserListReq(Message):
    pass

class UserListResp(Message):
    users: list[tuple[str,str]]
    pass

class ChannelListReq(Message):
    channel: str
    pass

class ChannelListResp(Message):
    channels: list[tuple[str,str]]
    pass

class ChatMessage(Message):
    author: str|None
    content: str
    channel: str|None
    id: str|None
    date: float|None
    pass

class ChatMessageConfirm(Message):
    message:MessageInfo
    pass

class DeleteMessage(Message):
    id: str
    pass

class EditMessage(Message):
    id: str
    content: str
    pass

class MessageHistoryReq(Message):
    channel: str
    pass

class MessageHistoryResp(Message):
    messages: list[MessageInfo]
    pass

class SetChannelSubscription(Message):
    channel: str|None
    state: bool
    pass

class Heartbeat(Message):
    pass

class HeartbeatAck(Message):
    pass

class JoinRegister(Message):
    name: str
    pass

class JoinRegisterResp(Message):
    id: str
    pass

class AddChannel(Message):
    name: str
    pass

class AddChannelResponse(Message):
    id: str
    pass

class RemoveChannel(Message):
    id: str
    pass

class NewChannel(Message):
    id: str
    name: str
    pass

class ChannelRemoved(Message):
    id: str
    pass

TYPE_STRS = {
    ConfirmResp:"OK",
    ErrorResp:"ERR",

    JoinRegister:"JOIN_REGISTER",
    Heartbeat:"HEART",
    HeartbeatAck:"BEAT",
    JoinMessage:"USER_JOIN",
    LeaveMessage:"USER_LEAVE",
    UserListReq:"USER_LIST_REQ",
    UserListResp:"USER_LIST_RESP",
    ChannelListReq:"CHANNEL_LIST_REQ",
    ChannelListResp:"CHANNEL_LIST_RESP",
    ChatMessage:"MESSAGE_SEND",
    ChatMessageConfirm:"MESSAGE_CONFIRM",
    EditMessage:"MESSAGE_EDIT",
    DeleteMessage:"MESSAGE_DELETE",
    SetChannelSubscription:"SET_CHANNEL_SUBSCRIPTION",
    MessageHistoryReq:"HISTORY_REQ",
    MessageHistoryResp:"HISTORY_RESP",
    AddChannel:"CHANNEL_ADD_REQ",
    AddChannelResponse:"CHANNEL_ADD_RESP",
    RemoveChannel:"CHANNEL_REM_REQ",
    NewChannel:"CHANNEL_ADD_NOTIFY",
    ChannelRemoved:"CHANNEL_REM_NOTIFY"
}

def base_message(type: str, request_id: int, **others) -> Message:
    return {
        "type":type,
        "request_id":request_id
        **others
    }
    pass

## Server side messages

def error_message(req_id: int, code: int, error_msg: str, **additional):
    return {
        "type":TYPE_STRS[ErrorResp],
        "request_id":req_id,
        "code":code,
        "message":error_msg,
        **additional
    }
    pass

def ok_message(req_id: int) -> ConfirmResp:
    return {
        "type":TYPE_STRS[ConfirmResp],
        "request_id":req_id,
    }
    pass

def join_message(req_id: int, user_id: str, user_name: str) -> JoinMessage:
    return {
        "type":TYPE_STRS[JoinMessage],
        "request_id":req_id,
        "data":{
            "id":user_id,
            "name":user_name
        }
    }
    pass

def leave_message(req_id: int, user_id: str) -> LeaveMessage:
    return {
        "type":TYPE_STRS[LeaveMessage],
        "request_id":req_id,
        "user":user_id
    }
    pass

def user_list_resp(req_id: int, users : list[tuple[str,str]]) -> UserListResp:
    return {
        "type":TYPE_STRS[UserListResp],
        "request_id":req_id,
        "users":users
    }
    pass

def channel_list_resp(req_id: int, channels : list[tuple[str,str]]) -> ChannelListResp:
    return {
        "type":TYPE_STRS[ChannelListResp],
        "request_id":req_id,
        "channels":channels
    }
    pass

def send_message_server(message_id: str, author_id: str, channel_id: str, date: float, content: str) -> ChatMessage:
    return {
        "type":TYPE_STRS[ChatMessage],
        "request_id":None,
        "channel":channel_id,
        "content":content,
        "author":author_id,
        "id":message_id,
        "date":date,
    }
    pass

def confirm_message(req_id: int, message_id: str, author_id: str, channel_id: str, date: float) -> ChatMessageConfirm:
    return {
        "type":TYPE_STRS[ChatMessageConfirm],
        "request_id":req_id,
        "message":{
            "id":message_id,
            "author":author_id,
            "channel":channel_id,
            "date":date,
            "content":None,
        }
    }
    pass

def heartbeat_ack(req_id: int) -> HeartbeatAck:
    return {
        "type":TYPE_STRS[HeartbeatAck],
        "request_id":req_id
    }
    pass

def message_history_resp(req_id: int, messages: list[MessageInfo]) -> MessageHistoryResp:
    return {
        "type":TYPE_STRS[MessageHistoryResp],
        "request_id":req_id,
        "messages":messages
    }
    pass

def add_channel_resp(req_id: int, channel_id: str) -> AddChannelResponse:
    return {
        "type":TYPE_STRS[AddChannelResponse],
        "request_id":req_id,
        "id":channel_id
    }
    pass

def add_channel_notify(channel_id: str, channel_name: str) -> NewChannel:
    return {
        "type":TYPE_STRS[NewChannel],
        "request_id":None,
        "id":channel_id,
        "name":channel_name
    }
    pass

def rem_channel_notify(channel_id: str) -> ChannelRemoved:
    return {
        "type":TYPE_STRS[NewChannel],
        "request_id":None,
        "id":channel_id
    }
    pass


## Client side messages

def base_client_msg(type: str, **others) -> tuple[Message, int]:
    luid = get_luid()
    return {
        "type":type,
        "request_id": luid,
        **others
    }, luid
    pass

def list_channel_req() -> tuple[ChannelListReq,int]:
    return base_client_msg(TYPE_STRS[ChannelListReq])
    pass

def send_message_client(channel_id: int, content: str) -> tuple[ChatMessage,int]:
    return base_client_msg(TYPE_STRS[ChatMessage], channel=channel_id, content=content, author=None, id=None)
    pass

def set_channel_subscription(channel_id: int, state: bool) -> tuple[SetChannelSubscription,int]:
    return base_client_msg(TYPE_STRS[SetChannelSubscription],channel=channel_id,state=state)
    pass

def heartbeat() -> tuple[Heartbeat, int]:
    return base_client_msg(TYPE_STRS[Heartbeat])
    pass

def list_user_req() -> UserListReq:
    return base_client_msg(TYPE_STRS[UserListReq])
    pass


## Snowflakes
from time import time_ns

__next_luid__ = 0
def get_luid() -> int:
    global __next_luid__

    luid = __next_luid__
    __next_luid__ += 1

    return luid
    pass

__snowflake_inc__ = 0
def generate_snowflake() -> str:
    global __snowflake_inc__
    
    epoch_millis = time_ns()//1000

    snowflake = epoch_millis << 8 + __snowflake_inc__

    __snowflake_inc__ = (__snowflake_inc__+1)%256

    return str(snowflake)
    pass