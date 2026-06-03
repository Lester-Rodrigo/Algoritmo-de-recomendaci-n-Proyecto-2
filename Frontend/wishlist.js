const API =
    "http://localhost:8000/api";

const username =
    localStorage.getItem("username");

async function searchGames(){

    const query =
        document.getElementById("search").value;

    const response =
        await fetch(
            `${API}/games/search?q=${query}`
        );

    const games =
        await response.json();

    renderResults(games);
}

function renderResults(games){

    const div =
        document.getElementById("results");

    div.innerHTML = "";

    games.forEach(game => {

        div.innerHTML += `
        <div class="game-card">

            <b>${game.name}</b>

            <button
                onclick="addToWishlist(${game.appid})">

                ❤️ Wishlist

            </button>

        </div>
        `;
    });
}

async function addToWishlist(appid){

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

    loadWishlist();
}

async function loadWishlist(){

    const response =
        await fetch(
            `${API}/wishlist/${username}`
        );

    const games =
        await response.json();

    const div =
        document.getElementById("wishlist");

    div.innerHTML = "";

    games.forEach(game => {

        div.innerHTML += `
        <div class="game-card">

            <b>${game.name}</b>

            <button
                onclick="removeWishlist(${game.appid})">

                Eliminar

            </button>

        </div>
        `;
    });
}

async function removeWishlist(appid){

    await fetch(
        `${API}/wishlist/remove`,
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

    loadWishlist();
}
