ERRORS = {
    "MALFORMED_PACKET":0b00000000000000000000000000000000,
    "NO_LOGIN":0b00000000000000000000000000010000,
    "DUPLICATE_NAME":0b00000000000000000000000000010001,
    "DUPLICATE_LOGIN":0b00000000000000000000000000010010,
    "UNKNOWN_CHANNEL":0b00000000000000000000000000100000,
}

from typing import TypedDict

class JoinInfo(TypedDict):
    id: int
    name: str
    pass

class MessageInfo(TypedDict):
    id: int
    author: int
    channel: int
    content: str
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
    user: int
    pass

class UserListReq(Message):
    pass

class UserListResp(Message):
    users: list[tuple[int,str]]
    pass

class ChannelListReq(Message):
    channel: int
    pass

class ChannelListResp(Message):
    data: list[tuple[int,str]]
    pass

class ChatMessage(Message):
    author: int|None
    content: str
    channel: int|None
    id: int|None
    pass

class ChatMessageConfirm(Message):
    id: int
    pass

class DeleteMessage(Message):
    id: int
    pass

class EditMessage(Message):
    id: int
    content: str
    pass

class MessageHistoryReq(Message):
    pass

class MessageHistoryResp(Message):
    messages: list[MessageInfo]
    pass

class SetChannelSubscription(Message):
    channel: int|None
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
    id: int
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
    MessageHistoryReq:"HISTORY_RESP",
    MessageHistoryResp:"HISTORY_RESP"
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

def join_message(req_id: int, user_id: int, user_name: str) -> JoinMessage:
    return {
        "type":TYPE_STRS[JoinMessage],
        "request_id":req_id,
        "data":{
            "id":user_id,
            "user_name":user_name
        }
    }
    pass

def leave_message(req_id: int, user_id: int) -> LeaveMessage:
    return {
        "type":TYPE_STRS[LeaveMessage],
        "request_id":req_id,
        "user":user_id
    }
    pass

def user_list_resp(req_id: int, users : list[tuple[int,str]]) -> UserListResp:
    return {
        "type":TYPE_STRS[UserListResp],
        "request_id":req_id,
        "users":users
    }
    pass

def channel_list_resp(req_id: int, channels : list[tuple[int,str]]) -> ChannelListResp:
    return {
        "type":TYPE_STRS[ChannelListResp],
        "request_id":req_id,
        "data":channels
    }
    pass

def send_message_server(message_id: int, author_id: int, channel_id: int, content: str) -> ChatMessage:
    return {
        "type":TYPE_STRS[ChatMessage],
        "request_id":None,
        "channel":channel_id,
        "content":content,
        "author":author_id,
        "id":message_id
    }
    pass

def confirm_message(req_id: int, message_id: int) -> ChatMessageConfirm:
    return {
        "type":TYPE_STRS[ChatMessageConfirm],
        "request_id":req_id,
        "id":message_id
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
        "type":TYPE_STRS[MessageHistoryResp]
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
def generate_snowflake() -> int:
    global __snowflake_inc__
    
    epoch_millis = time_ns()//1000

    snowflake = epoch_millis << 8 + __snowflake_inc__

    __snowflake_inc__ = (__snowflake_inc__+1)%256

    return snowflake
    pass