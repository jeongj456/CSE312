function update_posts(post_message) { 
    const message_id = document.getElementById("post_id");
    const message_subject = document.getElementById("subject1");
    const message_body = document.getElementById("body_placeholder");
    
    message_id.innerHTML = post_message[post_message.length -1]["ID"];
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
            if (message.length != 0) { update_posts(message); }
        }
    }
    
    request.open("GET", "/startup");
    request.send();
}
document.get

function arrow_up() {
    const request = new XMLHttpRequest();

    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 
            const message = JSON.parse(this.response);
            if (message.length != 0) { 
                post_id = Number(document.getElementById("post_id").innerHTML);
                if (post_id != -1 && post_id < message.length - 1) { update_posts(Array(message[post_id + 1])); }
             }
        }
    }
    
    request.open("GET", "/startup");
    request.send();
}


function arrow_down() {
    const request = new XMLHttpRequest();

    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 
            const message = JSON.parse(this.response);
            if (message.length != 0) {
                post_id = Number(document.getElementById("post_id").innerHTML);
                if (post_id != -1 && post_id > 0) { update_posts(Array(message[post_id - 1])); }
             }
        }
    }
    
    request.open("GET", "/startup");
    request.send();
}
