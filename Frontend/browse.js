const API =
    "http://localhost:8000/api";

const username =
    localStorage.getItem("username");
    
async function loadGames(){

    const response =
        await fetch(
            `${API}/games`
        );

    const games =
        await response.json();

    renderGames(games);
}
async function searchGames(){

    const query =
        document.getElementById("search").value;

    const response =
        await fetch(
            `${API}/games/search?q=${query}`
        );

    const games =
        await response.json();

    renderGames(games);
}
async function loadGenres(){

    const response =
        await fetch(
            `${API}/genres`
        );

    const genres =
        await response.json();

    const select =
        document.getElementById(
            "genreSelect"
        );

    genres.forEach(genre => {

        select.innerHTML += `
            <option value="${genre}">
                ${genre}
            </option>
        `;
    });
}
async function filterGenre(){

    const genre =
        document.getElementById(
            "genreSelect"
        ).value;

    const response =
        await fetch(
            `${API}/games/genre/${genre}`
        );

    const games =
        await response.json();

    renderGames(games);
}
function renderGames(games){

    const container =
        document.getElementById(
            "gamesContainer"
        );

    container.innerHTML = "";

    games.forEach(game => {

        container.innerHTML += `

        <div class="game-card">

            <h3>${game.name}</h3>

            <p>
                AppID: ${game.appid}
            </p>

            <p>
                ${game.genres || ""}
            </p>

            <div class="actions">

                <button
                    onclick="addLibrary(${game.appid})">

                    Biblioteca

                </button>

                <button
                    onclick="addWishlist(${game.appid})">

                    Wishlist

                </button>

                <button
                    onclick="likeGame(${game.appid})">

                    👍

                </button>

                <button
                    onclick="dislikeGame(${game.appid})">

                    👎

                </button>

            </div>

        </div>
        `;
    });
}
async function addLibrary(appid){

    await fetch(
        `${API}/library/add`,
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username,
                appid
            })
        }
    );

    alert("Agregado a biblioteca");
}
async function addWishlist(appid){

    await fetch(
        `${API}/wishlist/add`,
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username,
                appid
            })
        }
    );

    alert("Agregado a wishlist");
}
async function likeGame(appid){

    await fetch(
        `${API}/library/like`,
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username,
                appid
            })
        }
    );
}
