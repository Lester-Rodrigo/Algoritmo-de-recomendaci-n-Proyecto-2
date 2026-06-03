const API = "/api";
const username = localStorage.getItem("username");

window.onload = () => {
    loadLibrary();
    loadRecommendations();
};

async function searchGames() {
    const q = document.getElementById("search").value;
    if (!q) return;
    const response = await fetch(`${API}/games/search?q=${encodeURIComponent(q)}`);
    const games = await response.json();
    renderResults(games);
}

function renderResults(games) {
    const div = document.getElementById("results");
    div.innerHTML = "";
    games.forEach(game => {
        div.innerHTML += `
        <div class="game-card">
            <b>${game.name}</b>
            <button onclick="rateGame(${game.appid})">⭐ Rate</button>
            <button onclick="likeGame(${game.appid})">👍</button>
            <button onclick="dislikeGame(${game.appid})">👎</button>
            <button onclick="addWishlist(${game.appid})">❤️ Wishlist</button>
        </div>`;
    });
}

async function loadLibrary() {
    // library = games the user has rated
    const response = await fetch(`${API}/ratings/${username}`);
    const games = await response.json();
    const div = document.getElementById("library");
    div.innerHTML = "";

    if (!games.length) {
        div.innerHTML = "<p>No games rated yet. Search above to find games!</p>";
        return;
    }

    games.forEach(game => {
        div.innerHTML += `
        <div class="game-card">
            <b>${game.name}</b>
            <span>Score: ${game.score}/10</span>
            <button onclick="likeGame(${game.appid})">👍</button>
            <button onclick="dislikeGame(${game.appid})">👎</button>
        </div>`;
    });
}

async function rateGame(appid) {
    const score = prompt("Rate this game (1-10):");
    if (!score || isNaN(score) || score < 1 || score > 10) return;
    await fetch(`${API}/ratings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid, score: parseFloat(score) })
    });
    loadLibrary();
    loadRecommendations();
}

async function likeGame(appid) {
    await fetch(`${API}/reactions/like`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    loadRecommendations();
}

async function dislikeGame(appid) {
    await fetch(`${API}/reactions/dislike`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    loadRecommendations();
}

async function addWishlist(appid) {
    await fetch(`${API}/wishlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    alert("Added to wishlist!");
}

async function loadRecommendations() {
    // try hybrid first, fall back to genre-based for new users
    const response = await fetch(`${API}/recommendations/hybrid/${username}`);
    const games = await response.json();
    const div = document.getElementById("recommendations");
    div.innerHTML = "";

    if (!games.length) {
        div.innerHTML = "<p>Rate or like some games to get recommendations!</p>";
        return;
    }

    games.forEach(game => {
        div.innerHTML += `
        <div class="game-card">
            <b>${game.game}</b>
            <span>$${game.price ?? "—"}</span>
            <button onclick="addWishlist(${game.appid})">❤️ Wishlist</button>
        </div>`;
    });
}