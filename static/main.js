function update_posts(post_message) { 
    const message_id = document.getElementById("post_id");
    const message_subject = document.getElementById("subject1");
    const message_body = document.getElementById("body_placeholder");
    
    document.getElementById("post_id").setAttribute("value", post_message[post_message.length - 1]["ID"]);
    message_subject.innerHTML = post_message[post_message.length - 1]["subject"];
    message_body.innerHTML = post_message[post_message.length - 1]["creator"] + ": " + post_message[post_message.length - 1]["body"];
}


function startup() { 
    const explore = document.getElementById("modifybyJS");
    explore.innerHTML = "EXPLORE"; 

    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 

            const message = JSON.parse(this.response);
            if (message.length != 0) { 

                if (Number(document.getElementById("post_id")["value"]) == -1) { update_posts(message); }
                else { update_posts(Array(message[Number(document.getElementById("post_id")["value"])])); }
                getcomments();
            }
        }
    }
    
    request.open("GET", "/startup");
    request.send();   
}


function arrow_up() { arrow_control(1) }
function arrow_down() { arrow_control(-1) }

function arrow_control(arrow_direction) {

    // Create request and wait to recieve response
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 

            // TODO write what message represents
            const message = JSON.parse(this.response);

            // Get the post id, check a message exists, and that there is a above/below it based on arrow direction
            const post_id = Number(document.getElementById("post_id")["value"]);
            if ((arrow_direction == -1 && post_id != -1 && post_id > 0) || 
            (arrow_direction == 1 && post_id != -1 && message.length != 0 && post_id < message.length - 1)) { 

                // TODO comment, increment/decrement post_id, and displpay the new message details
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

            // TODO figure out what message is and check it is not empty
            const message = JSON.parse(this.response);
            console.log(message);
            if (message.length != 0) {

                // Clear comment box
                const comment_box = document.getElementById("comment_box");
                comment_box.innerHTML = "";

                // Write all messages specific to post in comment box
                for (let i = 0; i < message.length; i++) { 
                    comment_box.innerHTML += message[i]["postowner"] + ": " + message[i]["body"] + "<br>";
                }
            }

        }
    }

    // open and send the request with the specific post_id included in the route
    request.open("GET", "/getcomments/" + Number(document.getElementById("post_id")["value"]));
    request.send();
}


function modify_local() {

    // Create request and wait to recieve response
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 

            // TODO figure out what this represents
            Number(document.getElementById("post_id")["value"]) = JSON.parse(this.response);
        }
    }
    
    // open and send request to route modify_local
    request.open("GET", "/modify_local");
    request.send();
}