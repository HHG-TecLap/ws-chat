const HEARTBEAT_INTERVAL = 1000*60;
const HEARTBEAT_TIMEOUT  = 1000*10;
const ERRORS = {
    "MALFORMED_PACKET": 0b00000000000000000000000000000000,
    "NO_LOGIN":         0b00000000000000000000000000010000,
    "DUPLICATE_NAME":   0b00000000000000000000000000010001,
    "DUPLICATE_LOGIN":  0b00000000000000000000000000010010,
    "INVALID_NAME":     0b00000000000000000000000000010011,
    "UNKNOWN_CHANNEL":  0b00000000000000000000000000100000,
    "EMPTY_MESSAGE":    0b00000000000000000000000001000000,
};

const ws_constructor = () => {
    return new WebSocket(`ws://${location.host}/ws`);
}

var ws = ws_constructor();
var user_name, user_id, current_channel_id;
var USERS = {};
var CHANNELS = [];
var CHANNEL_HISTORY = {};

/**
 * Function to get a human-readable name
 * @param {Date} date 
 * @returns {string} Date String
 */
function parse_date(date){
    const currentDate = new Date();
    if (date.getMonth() === currentDate.getMonth() && date.getDay() === currentDate.getDay() && date.getFullYear() === currentDate.getFullYear()) {
        todayInLocaleString = '';
        console.log(navigator.language);
        switch (navigator.language) {
            case 'de': // Firefox
                todayInLocaleString = 'Heute, ';
                break;

            case 'de-DE': // Chrome
                todayInLocaleString = 'Heute, ';

            default:
                todayInLocaleString = 'Today, ';
                break;
        }
        return `${todayInLocaleString}${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
    } else {
        return date.toLocaleString(navigator.language);
    }
}

function add_message(message_info) {
    let date = new Date(message_info.date*1000);

    let chat_container = document.getElementById("chat");

    let message_container = document.createElement("div");
    message_container.className = "chat_messsage";

    // Meta data
    let message_meta = document.createElement("div");
    message_meta.className = "chat_meta";

    let author_span = document.createElement("span");
    author_span.className = "chat_author";
    let author_name = USERS[message_info.author] || message_info.username || "Unknown Author";
    author_span.innerText = author_name;
    if (!USERS[message_info.author]) author_span.style = "font-style: italic";

    let seperator_span = document.createElement("span");
    seperator_span.innerHTML = " <b>---</b> ";

    let time_span = document.createElement("span");
    time_span.className = "chat_time";
    time_span.innerText = parse_date(date);

    message_meta.appendChild(author_span);
    message_meta.appendChild(seperator_span);
    message_meta.appendChild(time_span);

    // Content
    let message_content = document.createElement("div");
    message_content.className = "chat_content";
    message_content.innerText = message_info.content;

    // Combine
    message_container.appendChild(message_meta);
    message_container.appendChild(message_content);

    chat_container.appendChild(message_container);

    // Scroll
    message_container.scrollIntoView(false);
}

function find_channel_name(id) {
    let name;
    CHANNELS.forEach(([cid, cname]) => {
        if (name != undefined) return;
        if (cid == id) name = cname;
        return;
    });

    return name;
}

function change_messages(messages){
    remove_children(document.getElementById("chat"));
    messages.forEach(add_message);
}

function switch_channel(id) {
    return event => {
        if(current_channel_id == undefined){
            let textarea = document.getElementById("msg_content");
            let button = document.getElementById("msg_submit");

            textarea.disabled = false;
            button.disabled = false;
        }

        let checkbox;
        let channel_list = document.getElementById("channel_list");
        channel_list.childNodes.forEach(node => {
            if (node.dataset.cid == id){
                checkbox = node.getElementsByTagName("input")[0];
            }
        });
        if(!checkbox.checked) checkbox.click();

        current_channel_id = id;
        if (CHANNEL_HISTORY[id] == undefined){
            let f = async function(){
                let [packet, luid] = message_history(id);
                
                let response;
                try{
                    response = await send_and_wait(packet,luid);
                } catch(response){
                    if (response.code == 0b00000000000000000000000000100000){
                        console.error(`The channel with the id ${id} does not exist. This should not occur`);
                        return;
                    }
                }
                CHANNEL_HISTORY[id] = response.messages;
                change_messages(response.messages);
            };
            f();
        } else{
        console.dir(CHANNEL_HISTORY[id]);
        change_messages(CHANNEL_HISTORY[id]);
	}

        let cname = find_channel_name(id);
        
        let channel_name = document.getElementById("channel_name");
        channel_name.innerText = cname;
    }
}
function set_subscription_event(id) {
    return async function(event){
        event.preventDefault();

        let channel_list = document.getElementById("channel_list");
        let checkbox;
        channel_list.childNodes.forEach(node => {
            let cid = node.dataset["cid"];
            if (id != cid) return;

            checkbox = node.getElementsByTagName("input")[0];
        });
        let new_state = checkbox.checked;
        console.log(new_state);

        let [packet, luid] = set_channel_subscription(id,new_state);
        
        try{
            await send_and_wait(packet, luid);
        } catch (response){
            if (response.code == 0b00000000000000000000000000100000){
                console.error(`Set Channel subscription returned unknown channel error. ID ${id}`);
            } else{
                console.error("Unexpected error message for set channel subscription");
                console.dir(response);
            }
            return;
        }
        if(!new_state){
            delete CHANNEL_HISTORY[id];
        } else{
            CHANNEL_HISTORY[id] = [];
            console.log(CHANNEL_HISTORY);
        }

        checkbox.checked = !checkbox.checked;
    };
}

function remove_children(obj) {
    while(obj.lastChild != null) obj.removeChild(obj.lastChild);
}

function send_and_wait(packet, luid) {
    let promise = new Promise((resolve, reject) => {
        let listener = event => {
            let response = JSON.parse(event.data);
            if(response.request_id != luid) return;
            
            ws.removeEventListener("message", listener);
            if (response.type == "ERR") reject(response);
            else resolve(response);
        }
        ws.addEventListener("message", listener);
        ws.send(JSON.stringify(packet));
    });

    return promise;
}

function single_beat() {
    let [packet, luid] = heartbeat();

    let promise = new Promise((resolve, reject) => {
        let listener = event => {
            let response = JSON.parse(event.data);
            if(response.request_id != luid) return;

            ws.removeEventListener("message",listener);
            resolve(response)
        }

        ws.addEventListener("message", listener);
        ws.send(JSON.stringify(packet));

        setTimeout(() => {
            ws.removeEventListener("message", listener);
            reject();
        }, HEARTBEAT_TIMEOUT);
    });

    return promise;
}

function create_list_item(name) {
    let item = document.createElement("li");
    item.innerText = name;
    return item;
}
function create_channel_item(id, name){
    let list_item = document.createElement("li");
    list_item.dataset["cid"]=id;
    
    let name_span = document.createElement("span");
    name_span.className="channel_name";
    name_span.innerText = name;
    list_item.appendChild(name_span);

    let checkbox_input = document.createElement("input");
    checkbox_input.type="checkbox";
    list_item.appendChild(checkbox_input);

    name_span.onclick=switch_channel(id);
    checkbox_input.onclick=set_subscription_event(id);

    return list_item;
}
function create_user_item(id, name) {
    let item = create_list_item(name);
    item.dataset["uid"] = id;
    return item;
}

async function update_user_list() {
    let [packet, luid] = request_user_list();
    let response;
    try{
        response = await send_and_wait(packet, luid);
    } catch (response){
        console.error("An error occured whilst updating the user list");
        console.dir(response);
        return;
    }
    
    if (response.type!="USER_LIST_RESP"){
        console.error(`Unexpected response whilst updating user list. Got type ${response.type}`);
        return;
    }

    let user_list = document.getElementById("user_list");

    remove_children(user_list);
    response.users.forEach(([uid, uname]) => {
        USERS[uid] = uname;
        let item = create_user_item(uid, uname);
        user_list.appendChild(item);
    });
}

async function update_channel_list() {
    let [packet, luid] = request_channel_list();
    let response;
    try{
        response = await send_and_wait(packet,luid);
    } catch (response){
        console.error("An error occured whilst updating th channel list");
        console.dir(response);
        return;
    }

    if (response.type!="CHANNEL_LIST_RESP"){
        console.error(`Unexpected response whilst updating the channel list. Got type ${response.type}`);
        return;
    }

    let channel_list = document.getElementById("channel_list");
    CHANNELS = response.channels;
    
    remove_children(channel_list);
    CHANNELS.forEach(([cid, cname]) => {
        let item = create_channel_item(cid, cname);
        channel_list.appendChild(item);
    })
}

const on_login = () => {
    let interval_number = setInterval(async function(){
        try{
            await single_beat();
        } catch{
            console.warn("Heartbeat timed out. Attempting to reconnect...");
            clearInterval(interval_number);
            on_timeout();
        }
    }, HEARTBEAT_INTERVAL);

    ws.addEventListener("close",() => {
        console.warn("Connection closed unexpectedly. Attempting to reconnect...");
        clearInterval(interval_number);
        on_timeout();
    });

    ws.addEventListener("message",event => {
        let data = JSON.parse(event.data);
        if (data.request_id != null) return;

        let user_list = document.getElementById("user_list");
        let channel_list = document.getElementById("channel_list");

        switch(data.type){
            case "USER_JOIN":
                let {id, name} = data.data;
                USERS[id] = name;

                user_list.appendChild(create_user_item(id, name));
                break;
            
            case "USER_LEAVE":
                let user_id = data.user;
                
                delete USERS[user_id];
                user_list.childNodes.forEach(node => {
                    if (node.dataset["uid"] == user_id){
                        user_list.removeChild(node);
                    }
                });
                break;
            
            case "MESSAGE_SEND":
                let message_data = {
                    id:data.id,
                    author:data.author,
                    channel:data.channel,
                    content:data.content,
                    date:data.date
                }
                CHANNEL_HISTORY[data.channel].push(message_data);
                if (data.channel === current_channel_id){
                    add_message(message_data);
                }

                break;
        }
    });

    let message_form = document.getElementById("message_form");
    let message_input = document.getElementById("msg_content");
    message_form.onsubmit = async function(event){
        event.preventDefault();
        
        let content = message_input.value;
        if (!validate_message(content)) return; // Don't send empty messages

        let [packet, luid] = message(current_channel_id,content);
        let response;
        try{
            response = await send_and_wait(packet,luid);
        } catch(response){
            if (response.code === ERRORS["UNKNOWN_CHANNEL"]){
                console.error(`Unknown channel for send message. Current channel id ${current_channel_id}`);
            } else if (response.code === ERRORS["EMPTY_MESSAGE"]){
                console.error("Somehow sent empty message. This should not normally occur and is most likely an error in code");
            } else{
                console.error("Unexpected error message from send message");
                console.dir(response);
            }
            return;
        }

        response.message.content = content;

        add_message(response.message);
        CHANNEL_HISTORY[current_channel_id].push(response.message);
        message_input.value = '';
    }
    message_input.addEventListener("input", () => {
        document.getElementById("msg_submit")
        .disabled = !validate_message(message_input.value);
    });

    update_user_list();
    update_channel_list();
};

const on_timeout = () => {
    user_id = undefined;

    let overlay = document.getElementById("overlay_container");
    let timeout_error = document.getElementById("connection_timed_out");
    let button = overlay.getElementsByTagName("button")[0];
    let input = document.getElementById("login_uname");

    input.value = user_name;
    timeout_error.hidden = false;
    overlay.hidden = false;
    
    button.disabled = true;
    if (!ws.CLOSED) ws.close();
    ws = ws_constructor();
    button.disabled = false;
}

window.addEventListener("load", () =>{
    let login_form = document.getElementById("login_form");
    let name_input = document.getElementById("login_uname");
    let button = login_form.getElementsByTagName("button")[0];
    
    name_input.addEventListener("input", () => {
        let valid_name = make_valid_name(name_input.value);
        
        // Disable button if name is invalid
        button.disabled = valid_name === null; 
    });

    login_form.onsubmit = event => {
        event.preventDefault();
        
        let error_msg = document.getElementById("uname_duplicate");
        button.disabled = true;

        // This is technically optional since the server would do this itself
        let name = make_valid_name(name_input.value);
        if (name === null) return; // If null, the name is invalid, meaning we're not logging in
        
        let [packet, luid] = register_name(name);
        send_and_wait(packet,luid).then(response => {
            if(response.type != "USER_JOIN"){
                console.error(`Register got unexpected response type. Got ${response.type}`);
                return;
            }
            user_id = response.data.id;
            user_name = response.data.name;

            error_msg.hidden = true;
            
            let overlay = document.getElementById("overlay_container");
            overlay.hidden = true;

            on_login();
        }, response => {
            if (response.code != 0b00000000000000000000000000010001){
                console.error("Register got unexpected error code.");
                console.dir(response);
                return;
            }
            button.disabled = false;
            
            error_msg.hidden = false;
        });
    }

    // Emulate input event to cause initial check (helpful for autocompletes)
    name_input.dispatchEvent(new Event("input"));
    document.getElementById("msg_content")
    .dispatchEvent(new Event("input"));
});
