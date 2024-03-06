/*  update the value of a tag in the html file
    document.getElementById('name_of_specific_id').innerHTML = "Message you want it to be changed to" 
*/

/*  way to call this file in the html file   
    <script type="text/javascript" src="{{url_for('static', filename='main.js')}}"></script>
 */

// moved login and register into static because they couldn't be found in templates with current setup

function Logout() { window.location = "/static/login.html"; }
function register_page() { window.location = "/static/register.html"; }