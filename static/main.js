function update_posts(post_message) { 

    // change post_id to be the id of the post_message
    const post_id = document.getElementById("post_id");
    post_id.setAttribute("value", post_message[post_message.length - 1]["ID"]);

    // change subject1 to be the subject of post_message
    const message_subject = document.getElementById("subject1");
    message_subject.innerHTML = post_message[post_message.length - 1]["subject"];

    // change body_placeholder to be the body of post_message
    const message_body = document.getElementById("body_placeholder");
    message_body.innerHTML = post_message[post_message.length - 1]["creator"] + ": " + post_message[post_message.length - 1]["body"];
}


function startup() { 
    //Start the websocket logic.
    // socketlogic();

    // Modify webpage with js on refresh
    const explore = document.getElementById("modifybyJS");
    explore.innerHTML = "EXPLORE"; 

    // Create request and wait to recieve response
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 

            // Dictionary of message, containing subject, body, and post_id
            const message = JSON.parse(this.response);
            const post_id = Number(document.getElementById("post_id")["value"]);

            // TODO figure out what first part does and displpay message details
            if (post_id == -1) { update_posts(message); }
            else { update_posts(Array(message[post_id])); }
            getcomments();
        }
    }
    
    // open and send request to route /startup
    request.open("GET", "/startup");
    request.send();   
}

function socketlogic() {

    socket = new WebSocket('ws://' + window.location.host + '/websocket');

    socket.onmessage = function (message) {
        console.log("Finally got literally anything")
    }

}

// function handlemessage(message){
//     console.log(JSON.parse(message.data))
// }


function arrow_up() { arrow_control(1) }
function arrow_down() { arrow_control(-1) }

function arrow_control(arrow_direction) {

    // Create request and wait to recieve response
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 

            // Dictionary of message, containing subject, body, and post_id
            const message = JSON.parse(this.response);

            // Get the post id, check a message exists, and that there is a above/below it based on arrow direction
            const post_id = Number(document.getElementById("post_id")["value"]);

            if ((arrow_direction == -1 && post_id > 0) || (arrow_direction == 1 && message.length != 0 && post_id < message.length - 1)) { 
                // update server to remeber the user's last viewed post
                update_place(message[0]["viewer"], post_id + arrow_direction);    

                // update post subject, body, and id to message. Then increment/decrement post_id, and displpay new message details
                update_posts(Array(message[post_id + arrow_direction])); 
                document.getElementById("post_id").setAttribute("value", post_id + arrow_direction); 
                getcomments();
            }
        }
    }
    
    // open and send request to route /startup
    request.open("GET", "/startup");
    request.send();
}


function getcomments() {

    // Create request and wait to recieve response
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {

            // Dictionary of message containing owner and body
            const message = JSON.parse(this.response);

            // Clear comment box
            const comment_box = document.getElementById("comment_box");
            comment_box.innerHTML = "";

            // Write all messages specific to post in comment box
            for (let i = 0; i < message.length; i++) { 
                comment_box.innerHTML += message[i]["postowner"] + ": " + message[i]["body"] + "<br>";
            }

        }
    }

    // open and send the request with the specific post_id included in the route
    request.open("GET", "/getcomments/" + Number(document.getElementById("post_id")["value"]));
    request.send();
}

function update_place(username, place) { 

        // Create request
        const request = new XMLHttpRequest();
        request.onreadystatechange = function () { }
    
        // open and send the request with the user's username and post they were viewing
        request.open("GET", "/update_place/" + username + "/" + place);
        request.send();
}