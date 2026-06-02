const genres =
document.querySelectorAll(".genre-btn");

genres.forEach(btn => {

    btn.addEventListener("click", () => {

        btn.classList.toggle("selected");

    });

});

function goNextPage(){

    const selectedGenres =
        document.querySelectorAll(
            ".genre-btn.selected"
        );

    if(selectedGenres.length < 3){

        alert(
            "Please select at least 3 genres."
        );

        return;
    }

    window.location.href =
        "../html/profile.html";

}