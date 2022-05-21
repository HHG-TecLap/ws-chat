var __next_luid__ = 0;

const get_luid = () => {
    luid = __next_luid__;
    return luid;
}


// Client messages

const request_channel_list = () => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "CHANNEL_LIST_REQ"
    }, luid];
};

const request_user_list = () => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "USER_LIST_REQ"
    }, luid];
};

const message = (channel_id, content) => {
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

const set_channel_subscription = (channel_id, state) => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "SET_CHANNEL_SUBSCRIPTION",
        channel: channel_id,
        state: state
    }, luid];
};

const heartbeat = code => {
    let luid = get_luid();
    return [{
        request_id: luid,
        type: "HEART",
        code: code
    }, luid];
};

const message_history = channel => {
    let luid = get_luid();
    return [{
        type: "HISTORY_REQ",
        channel: channel
    }, luid];
}

// Server messages

const SERVER_MESSAGE_TYPES = [
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