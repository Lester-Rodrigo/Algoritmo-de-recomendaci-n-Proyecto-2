const API = "/api";
const username = localStorage.getItem("username");

window.onload = () => {
    loadGames();
    loadGenres();
};

async function loadGames() {
    const response = await fetch(`${API}/games`);
    const games = await response.json();
    renderGames(games);
}

async function searchGames() {
    const query = document.getElementById("search").value;
    if (!query) { loadGames(); return; }
    const response = await fetch(`${API}/games/search?q=${encodeURIComponent(query)}`);
    const games = await response.json();
    renderGames(games);
}

async function loadGenres() {
    const response = await fetch(`${API}/genres`);
    const genres = await response.json();
    const select = document.getElementById("genreSelect");
    genres.forEach(genre => {
        select.innerHTML += `<option value="${genre}">${genre}</option>`;
    });
}

async function filterGenre() {
    const genre = document.getElementById("genreSelect").value;
    if (!genre) { loadGames(); return; }
    // filter client-side from full list since there's no genre filter endpoint
    const response = await fetch(`${API}/games?limit=200`);
    const games = await response.json();
    // fetch each game's genres would be slow, so search by genre name instead
    const filtered = games.filter(g =>
        (g.genres || []).includes(genre)
    );
    renderGames(filtered.length ? filtered : games);
}

function renderGames(games) {
    const container = document.getElementById("gamesContainer");
    container.innerHTML = "";

    if (!games.length) {
        container.innerHTML = "<p>No games found.</p>";
        return;
    }

    games.forEach(async game => {
        const card = document.createElement("div");
        card.className = "game-card";
        card.innerHTML = `<h3>${game.name}</h3><p>$${game.price ?? "—"}</p>`;
        container.appendChild(card);

        // load cover asynchronously so the list appears instantly
        const media = await fetch(`/api/games/${game.appid}/media`).then(r => r.json());
        if (media.header_image) {
            card.insertAdjacentHTML("afterbegin", `<img src="${media.header_image}" alt="${game.name}">`);
        }
        if (media.short_description) {
            card.insertAdjacentHTML("beforeend", `<p class="desc">${media.short_description}</p>`);
        }
    });
}

async function addWishlist(appid) {
    const res = await fetch(`${API}/wishlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    if (res.ok) alert("Added to wishlist!");
}

async function likeGame(appid) {
    await fetch(`${API}/reactions/like`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
}

async function dislikeGame(appid) {
    await fetch(`${API}/reactions/dislike`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
}