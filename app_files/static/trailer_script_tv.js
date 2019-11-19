//tv trailer functions
var modal2 = document.getElementById("tv_trailer_box");
var btn2 = document.getElementById("tv_youtube_button");
var span2 = document.getElementsByClassName("tv_close_box")[0];

btn2.onclick = function() {
    modal2.style.display = "block";
}

span2.onclick = function() {
    modal2.style.display = "none";
}

window.addEventListener('click', function(event) {
    if (event.target == modal2) {
        modal2.style.display = "none";
    }
});