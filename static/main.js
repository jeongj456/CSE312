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
            if (message.length != 0) { 
                update_posts(message); 
                const post_id = Number(document.getElementById("post_id").innerHTML);
                const postID = document.getElementById("postidhidden");
                postID.setAttribute("value", post_id);
                getcomments();
            }
        }
    }
    
    request.open("GET", "/startup");
    request.send();
    
}

function arrow_up() {
    const request = new XMLHttpRequest();

    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) { 
            const message = JSON.parse(this.response);
            if (message.length != 0) { 
                const post_id = Number(document.getElementById("post_id").innerHTML);
                const postID = document.getElementById("postidhidden");
                postID.setAttribute("value", post_id);
                if (post_id != -1 && post_id < message.length - 1) { 
                    update_posts(Array(message[post_id + 1])); 
                    postID.setAttribute("value", post_id+1); 
                    getcomments();
                }
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
                const post_id = Number(document.getElementById("post_id").innerHTML);
                const postID = document.getElementById("postidhidden");
                postID.setAttribute("value", post_id);
                if (post_id != -1 && post_id > 0) { 
                    update_posts(Array(message[post_id - 1])); 
                    postID.setAttribute("value", post_id-1); 
                    getcomments();
                }
             }
        }
    }
    
    request.open("GET", "/startup");
    request.send();
}

function getcomments(){
    let route = "/getcomments/"
    route += Number(document.getElementById("post_id").innerHTML);

    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const message = JSON.parse(this.response);
            console.log(message);
            if (message.length != 0) {
                const idk = document.getElementById("comment_box");
                idk.innerHTML = "";
                for (let i = 0; i < message.length; i++) { 
                    idk.innerHTML += message[i]["postowner"] + ": " + message[i]["body"] + "<br>";
                }
            }
            else{
                const idk = document.getElementById("comment_box");
                idk.innerHTML = "";
            }
        }
    }

    request.open("GET", route);
    request.send();

    // Get the post id and concatenate it to the end of route
    // make a call to the server at the route now stored in that variable
    // this (should) return to you a list of all comments for that post
    // return that list for usage.
    //My idea behind this is that whenever the post is changed, you can call this function
    // to get the comments for a post and then from that you can populate the comments section as a list.
}