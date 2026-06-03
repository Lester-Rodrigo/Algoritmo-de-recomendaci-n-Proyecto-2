async function goNextPage() {

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

    const genres =
        Array.from(selectedGenres)
        .map(btn => btn.textContent);

    try {

        const response = await fetch(
            "/api/genres",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    genres: genres
                })
            }
        );

        const username =
            localStorage.getItem("username");

        await fetch("/api/user/genres",
            {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({
                    username: username,
                    genres: genres
                })
            }
        );

        window.location.href =
            "/static/html/profile.html";

    } catch(error) {

        console.error(error);

        alert(
            "Error obtaining recommendations"
        );
    }
}