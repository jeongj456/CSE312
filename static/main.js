/*  update the value of a tag in the html file
    document.getElementById('name_of_specific_id').innerHTML = "Message you want it to be changed to" 
*/

/*  way to call this file in the html file   
    <script type="text/javascript" src="{{url_for('static', filename='main.js')}}"></script>
 */

// moved login and register into static because they couldn't be found in templates with current setup

function Startup() { document.getElementById("comments").innerHTML = "Add a Comment" }

function Login() { send_request("POST", "/login"); }

function Logout() { send_request("GET", "/logout"); }

function Register() { send_request("POST", "/register"); }

function send_request(method, path) {
    const request = new XMLHttpRequest();
    request.open(method, path);
    request.send(JSON.stringify());
 }