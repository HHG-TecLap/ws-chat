var get_luid, register_name, request_channel_list, request_user_list, message, set_channel_subscription, heartbeat, message_history, SERVER_MESSAGE_TYPES, make_valid_name;

var __next_luid__ = 0;

get_luid = () => {
    let luid = __next_luid__;
    __next_luid__++;
    return luid;
}

make_valid_name = name => {
    let new_name = name.trim()
    .split(" ")
    .filter(s => s.length != 0)
    .join(" ");

    return new_name.length != 0 ? new_name : null;
};


// Client messages

register_name = name => {
    let luid = get_luid();
    return [{
        type: "JOIN_REGISTER",
        request_id: luid,
        name: name
    }, luid];
}

request_channel_list = () => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "CHANNEL_LIST_REQ"
    }, luid];
};

request_user_list = () => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "USER_LIST_REQ"
    }, luid];
};

message = (channel_id, content) => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "MESSAGE_SEND",
        author:null,
        channel:channel_id,
        id:null,
        content:content
    }, luid];
};

set_channel_subscription = (channel_id, state) => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "SET_CHANNEL_SUBSCRIPTION",
        channel: channel_id,
        state: state
    }, luid];
};

heartbeat = code => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "HEART",
        code: code
    }, luid];
};

message_history = channel => {
    let luid = get_luid();
    return [{
        type: "HISTORY_REQ",
        request_id: luid,
        channel: channel
    }, luid];
}

// Server messages

SERVER_MESSAGE_TYPES = [
    "ERR",
    "OK",
    "BEAT",
    "USER_JOIN",
    "USER_LEAVE",
    "CHANNEL_LIST_RESP",
    "MESSAGE_SEND",
    "MESSAGE_CONFIRM",
    "USER_LIST_RESP",
    "HISTORY_RESP",
];