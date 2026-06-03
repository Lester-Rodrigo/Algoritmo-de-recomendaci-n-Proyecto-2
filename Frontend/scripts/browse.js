let searchTimer;

window.onload = () => {
    loadGames();
    loadGenres();
};

async function loadGames() {
    const res   = await fetch(`${API}/games?limit=60`);
    const games = await res.json();
    renderGames(games, "gamesContainer");
}

function debounceSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 300);
}

async function doSearch() {
    const q = document.getElementById("search").value.trim();
    if (!q) { loadGames(); return; }
    const res   = await fetch(`${API}/games/search?q=${encodeURIComponent(q)}`);
    const games = await res.json();
    renderGames(games, "gamesContainer");
}

async function loadGenres() {
    const res    = await fetch(`${API}/genres`);
    const genres = await res.json();
    const select = document.getElementById("genreSelect");
    genres.forEach(g => {
        select.innerHTML += `<option value="${g}">${g}</option>`;
    });
}

async function filterGenre() {
    const genre = document.getElementById("genreSelect").value;
    if (!genre) { loadGames(); return; }
    const res   = await fetch(`${API}/games/genre/${encodeURIComponent(genre)}`);
    const games = await res.json();
    renderGames(games, "gamesContainer");
}