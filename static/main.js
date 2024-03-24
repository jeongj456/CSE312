/*  update the value of a tag in the html file
    document.getElementById('name_of_specific_id').innerHTML = "Message you want it to be changed to" 
*/

/*  way to call this file in the html file   
    <script type="text/javascript" src="{{url_for('static', filename='main.js')}}"></script>
 */

// moved login and register into static because they couldn't be found in templates with current setup


function startup() { 
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    request.open("GET", "/startup")
}

