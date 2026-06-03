async function loadGames() {

    const response =
        await fetch(
            "http://localhost:8000/api/games"
        );

    const games =
        await response.json();

    console.log(games);

}