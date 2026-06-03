let searchTimer;

window.onload = () => {
    loadHero();
    loadRecommended();
};

async function loadHero() {
    const res   = await fetch(`${API}/games?limit=20`);
    const games = await res.json();
    if (!games.length) return;

    const heroGame = games[Math.floor(Math.random() * games.length)];
    document.getElementById("hero-title").textContent = heroGame.name;

    const media = await fetch(`${API}/games/${heroGame.appid}/media`).then(r => r.json());
    const hero  = document.getElementById("hero");

    if (media.background || media.header_image) {
        hero.style.backgroundImage = `linear-gradient(to right, rgba(7,11,29,.95) 35%, rgba(7,11,29,.4)), url('${media.background || media.header_image}')`;
        hero.style.backgroundSize = "cover";
        hero.style.backgroundPosition = "center";
    }

    if (media.short_description) {
        document.getElementById("hero-desc").textContent = media.short_description;
    }

    document.getElementById("hero-wishlist").onclick = () => wishlistGame(heroGame.appid);
    document.getElementById("hero-like").onclick     = () => likeGame(heroGame.appid);
}

async function loadRecommended() {
    let res   = await fetch(`${API}/recommendations/hybrid/${username}`);
    let games = await res.json();

    if (!games.length) {
        res   = await fetch(`${API}/recommendations/genres/${username}`);
        games = await res.json();
    }

    renderGames(games, "recommended");
}

function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 350);
}

async function doSearch() {
    const q       = document.getElementById("search").value.trim();
    const section = document.getElementById("search-results");
    if (!q) { section.style.display = "none"; return; }
    section.style.display = "block";
    const res   = await fetch(`${API}/games/search?q=${encodeURIComponent(q)}`);
    const games = await res.json();
    renderGames(games, "search-grid");
}