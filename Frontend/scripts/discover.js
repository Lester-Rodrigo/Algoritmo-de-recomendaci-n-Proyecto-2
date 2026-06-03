window.onload = async () => {
    loadSection(`${API}/recommendations/hybrid/${username}`,        "recommended");
    loadSection(`${API}/recommendations/genres/${username}`,        "wishlistBased");
    loadSection(`${API}/recommendations/collaborative/${username}`, "similarUsers");
};

async function loadSection(url, containerId) {
    const res   = await fetch(url);
    const games = await res.json();
    renderGames(games, containerId);
}