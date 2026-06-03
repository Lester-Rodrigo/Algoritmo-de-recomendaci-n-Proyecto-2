const API = "/api";
const username = localStorage.getItem("username");

// Show username in sidebar
const sidebarUser = document.getElementById("sidebar-user");
if (sidebarUser && username) {
    sidebarUser.textContent = `👤 ${username}`;
}

// Redirect to login if not logged in
if (!username &&
    !window.location.pathname.includes("login") &&
    !window.location.pathname.includes("register") &&
    !window.location.pathname.includes("selectgenre")) {
    window.location.href = "/static/html/login.html";
}



function makeGameCard(game, actions) {
    const appid = game.appid;
    const name  = game.name ?? game.game ?? "Unknown";
    const price = game.price != null ? `$${Number(game.price).toFixed(2)}` : "Free";

    const card = document.createElement("div");
    card.className = "game-card";
    card.dataset.appid = appid;

    card.innerHTML = `
        <div class="card-img-wrap">
            <div class="card-img-placeholder"></div>
            <img class="card-img" src="" alt="${name}" style="display:none">
        </div>
        <div class="game-card-body">
            <h3>${name}</h3>
            <span class="price">${price}</span>
            <p class="desc"></p>
        </div>
        <div class="game-card-actions">${actions ?? defaultActions(appid)}</div>
    `;

    // fetch image + description without blocking card render
    fetch(`${API}/games/${appid}/media`)
        .then(r => r.json())
        .then(media => {
            const img         = card.querySelector(".card-img");
            const placeholder = card.querySelector(".card-img-placeholder");
            const src = media.header_image || media.background || "";

            if (src) {
                img.onload = () => {
                    placeholder.style.display = "none";
                    img.style.display = "block";
                };
                img.onerror = () => {
                    placeholder.style.display = "none";
                };
                img.src = src;
            } else {
                placeholder.style.display = "none";
            }

            if (media.short_description) {
                card.querySelector(".desc").textContent = media.short_description;
            }
        })
        .catch(() => {
            card.querySelector(".card-img-placeholder").style.display = "none";
        });

    return card;
}

function defaultActions(appid) {
    return `
        <button class="btn btn-ghost btn-sm" onclick="wishlistGame(${appid})">❤️</button>
        <button class="btn btn-ghost btn-sm" onclick="likeGame(${appid})">👍</button>
        <button class="btn btn-ghost btn-sm" onclick="dislikeGame(${appid})">👎</button>
    `;
}

function renderGames(games, container, actionsFn) {
    if (typeof container === "string") container = document.getElementById(container);
    container.innerHTML = "";

    if (!games || !games.length) {
        container.innerHTML = `<div class="empty"><strong>Nothing here yet</strong>Interact with some games to get started.</div>`;
        return;
    }

    games.forEach(game => {
        const actions = actionsFn ? actionsFn(game) : defaultActions(game.appid);
        container.appendChild(makeGameCard(game, actions));
    });
}

// ── COMMON ACTIONS ────────────────────────────────────────────────────────────

async function wishlistGame(appid) {
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
}

async function dislikeGame(appid) {
    await fetch(`${API}/reactions/dislike`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, appid })
    });
}

function debounce(fn, ms = 350) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}