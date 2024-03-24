/*  update the value of a tag in the html file
    document.getElementById('name_of_specific_id').innerHTML = "Message you want it to be changed to" 
*/

/*  way to call this file in the html file   
    <script type="text/javascript" src="{{url_for('static', filename='main.js')}}"></script>
 */

// moved login and register into static because they couldn't be found in templates with current setup

function update_posts(post_message) { 
    console.log("printing a test print");

    if (post_message.length != 0) {
        console.log(post_message);
        console.log(post_message[postMessage.length - 1]);
        console.log(post_message[postMessage.length - 1]["body"]);
        console.log(post_message[postMessage.length - 1]["subject"])

        const message_body = document.getElementById("test_cat");
        const message_subject = document.getElementById("subject1");
    
        message_body.innerHTML += post_message[postMessage.length - 1]["body"];
        message_subject.innerHTML = post_message[postMessage.length - 1]["subject"];
    }
}

function startup() { 
    /* const explore = document.getElementsByClassName("explore-page");
    explore.innerHTML = "EXPLORE"; */

    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const message = JSON.parse(this.response);
            update_posts(message);
        }
    }
    
    request.open("GET", "/startup");
    request.send();
}

