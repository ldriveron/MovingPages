//movie trailer functions
var modal = document.getElementById("movie_trailer_box");
var btn = document.getElementById("movie_youtube_button");
var span = document.getElementsByClassName("movie_close_box")[0];

btn.onclick = function() {
    modal.style.display = "block";
}

span.onclick = function() {
    modal.style.display = "none";
}

window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
});