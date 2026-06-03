const API = "/api";
const username = localStorage.getItem("username");

window.onload = async () => {
    await loadRecommended();
    await loadWishlistBased();
    await loadSimilarUsers();
};

async function loadRecommended() {
    // hybrid = content-based + collaborative, falls back to genre prefs
    const response = await fetch(`${API}/recommendations/hybrid/${username}`);
    const games = await response.json();
    renderGames(games, "recommended");
}

async function loadWishlistBased() {
    // use genre recommendations as "wishlist-based" section
    const response = await fetch(`${API}/recommendations/genres/${username}`);
    const games = await response.json();
    renderGames(games, "wishlistBased");
}

async function loadSimilarUsers() {
    // collaborative filtering = games liked by similar users
    const response = await fetch(`${API}/recommendations/collaborative/${username}`);
    const games = await response.json();
    renderGames(games, "similarUsers");
}

function renderGames(games, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!games.length) {
        container.innerHTML = "<p>Nothing to show yet — rate or like some games!</p>";
        return;
    }

    games.forEach(game => {
        container.innerHTML += `
        <div class="game-card">
            <h3>${game.game ?? game.name}</h3>
            <p>$${game.price ?? "—"}</p>
            <div class="actions">
                <button onclick="addWishlist(${game.appid})">❤️ Wishlist</button>
                <button onclick="likeGame(${game.appid})">👍</button>
                <button onclick="dislikeGame(${game.appid})">👎</button>
            </div>
        </div>`;
    });
}

async function addWishlist(appid) {
    await fetch(`${API}/wishlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
}

async function likeGame(appid) {
    await fetch(`${API}/reactions/like`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    // reload all sections after interaction
    await loadRecommended();
}

async function dislikeGame(appid) {
    await fetch(`${API}/reactions/dislike`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    await loadRecommended();
}