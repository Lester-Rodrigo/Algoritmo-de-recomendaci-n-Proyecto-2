let searchTimer;

window.onload = () => {
    loadHero();
    loadSections();
};

async function loadHero() {
    const res   = await fetch(`${API}/games?limit=100`);
    const games = await res.json();
    if (!games.length) return;

    const heroGame = games[Math.floor(Math.random() * games.length)];
    document.getElementById("hero-title").textContent = heroGame.name;

    const media = await fetch(`${API}/games/${heroGame.appid}/media`).then(r => r.json());
    const hero  = document.getElementById("hero");

    if (media.background || media.header_image) {
        hero.style.backgroundImage = `linear-gradient(to right, rgba(7,11,29,.95) 5%, rgba(7,11,29,.0)), url('${media.background || media.header_image}')`;
        hero.style.backgroundSize = "cover";
        hero.style.backgroundPosition = "center";
    }

    if (media.short_description) {
        document.getElementById("hero-desc").textContent = media.short_description;
    }

    document.getElementById("hero-wishlist").onclick = () => wishlistGame(heroGame.appid);
    document.getElementById("hero-like").onclick     = () => likeGame(heroGame.appid);
}

async function loadSections() {

    
    let res = await fetch(`${API}/recommendations/hybrid/${username}`);
    let games = await res.json();
    renderGames(games, "recommended");

    
    const genres = await fetch(
        `${API}/user/genres/${username}`
    ).then(r => r.json());

    const genreContainer = document.getElementById("genre-sections");

    for (const genre of genres) {

        const safeId = genre.replace(/\s+/g, "-");

        const section = document.createElement("section");

        section.innerHTML = `
            <div class="section-title">${genre}</div>
            <div class="games-grid" id="genre-${safeId}"></div>
        `;

        genreContainer.appendChild(section);

        const genreGames = await fetch(
            `${API}/games/genre/${encodeURIComponent(genre)}?limit=10`
        ).then(r => r.json());

        renderGames(genreGames, `genre-${safeId}`);
    }

    // Similar users
    res = await fetch(`${API}/recommendations/collaborative/${username}`);
    games = await res.json();
    renderGames(games, "similarUsers");
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