// wishlist.js
let searchTimer;

window.onload = () => loadWishlist();

function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 350);
}

async function doSearch() {
    const q = document.getElementById("search").value.trim();
    if (!q) { document.getElementById("results").innerHTML = ""; return; }
    const res = await fetch(`${API}/games/search?q=${encodeURIComponent(q)}`);
    const games = await res.json();
    renderGames(games, "results", game => `
        <button class="btn btn-primary btn-sm" onclick="addToWishlist(${game.appid})">❤️ Add</button>
        <button class="btn btn-ghost btn-sm" onclick="likeGame(${game.appid})">👍</button>
        <button class="btn btn-ghost btn-sm" onclick="dislikeGame(${game.appid})">👎</button>
    `);
}

async function addToWishlist(appid) {
    await fetch(`${API}/wishlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
    loadWishlist();
}

async function loadWishlist() {
    const res   = await fetch(`${API}/wishlist/${username}`);
    const games = await res.json();
    renderGames(games, "wishlist", game => `
        <button class="btn btn-ghost btn-sm" onclick="removeFromWishlist(${game.appid})">🗑 Remove</button>
        <button class="btn btn-ghost btn-sm" onclick="likeGame(${game.appid})">👍</button>
    `);
}

async function removeFromWishlist(appid) {
    await fetch(`${API}/wishlist/${appid}?username=${username}`, { method: "DELETE" });
    loadWishlist();
}