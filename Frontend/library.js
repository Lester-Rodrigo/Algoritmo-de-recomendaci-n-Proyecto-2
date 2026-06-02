const API = "http://localhost:8000/api";

const username =
    localStorage.getItem("username");

async function searchGames(){

    const q =
        document.getElementById("search").value;

    const response =
        await fetch(
            `${API}/games/search?q=${q}`
        );

    const games =
        await response.json();

    renderResults(games);
}
function renderResults(games){

    const div =
        document.getElementById("results");

    div.innerHTML = "";

    games.forEach(game=>{

        div.innerHTML += `
        <div class="game-card">

            <b>${game.name}</b>

            <button
                onclick="addGame(${game.appid})">

                Agregar

            </button>

        </div>
        `;
    });
}
async function addGame(appid){

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

    loadLibrary();
}
async function loadLibrary(){

    const response =
        await fetch(
            `${API}/library/${username}`
        );

    const games =
        await response.json();

    const div =
        document.getElementById("library");

    div.innerHTML = "";

    games.forEach(game=>{

        div.innerHTML += `
        <div class="game-card">

            <b>${game.name}</b>

            <button
                onclick="likeGame(${game.appid})">

                👍

            </button>

            <button
                onclick="dislikeGame(${game.appid})">

                👎

            </button>

        </div>
        `;
    });
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

    loadRecommendations();
}
async function dislikeGame(appid){

    await fetch(
        `${API}/library/dislike`,
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

    loadRecommendations();
}
async function loadRecommendations(){

    const response =
        await fetch(
            `${API}/recommendations/preferences/${username}`
        );

    const games =
        await response.json();

    const div =
        document.getElementById(
            "recommendations"
        );

    div.innerHTML = "";

    games.forEach(game=>{

        div.innerHTML += `
        <div class="game-card">

            <b>${game.name}</b>

            <p>
                Score: ${game.score}
            </p>

        </div>
        `;
    });
}

loadLibrary();
loadRecommendations();