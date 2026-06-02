async function loadGames() {

    const response =
        await fetch(
            "/api/games"
        );

    const games =
        await response.json();

    console.log(games);

}