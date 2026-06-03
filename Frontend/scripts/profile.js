window.onload = () => {
    document.getElementById("profile-username").textContent = username;
    loadStats();
    loadLikesTab(); // default tab
};

// ── Avatar & banner ───────────────────────────────────────────────────────────
const avatar = document.getElementById("avatar");
const banner = document.getElementById("banner");

avatar.addEventListener("click", () => document.getElementById("avatarUpload").click());
banner.addEventListener("click", () => document.getElementById("bannerUpload").click());

document.getElementById("avatarUpload").addEventListener("change", function () {
    const reader = new FileReader();
    reader.onload = e => { avatar.src = e.target.result; };
    if (this.files[0]) reader.readAsDataURL(this.files[0]);
});

document.getElementById("bannerUpload").addEventListener("change", function () {
    const reader = new FileReader();
    reader.onload = e => {
        banner.style.backgroundImage = `url(${e.target.result})`;
        banner.style.backgroundSize = "cover";
        banner.style.backgroundPosition = "center";
    };
    if (this.files[0]) reader.readAsDataURL(this.files[0]);
});

// ── Tabs ──────────────────────────────────────────────────────────────────────
function showTab(id, btn) {
    document.querySelectorAll(".content > div").forEach(d => d.style.display = "none");
    document.getElementById(id).style.display = "block";
    document.querySelectorAll(".tabs button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    if (id === "wishlist-tab") loadWishlistTab();
    if (id === "genres-tab")   loadGenresTab();
}

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadStats() {
    const [reactions, wishlist] = await Promise.all([
        fetch(`${API}/reactions/${username}`).then(r => r.json()),
        fetch(`${API}/wishlist/${username}`).then(r => r.json()),
    ]);
    document.getElementById("stat-likes").textContent    = reactions.filter(r => r.reaction === "LIKED").length;
    document.getElementById("stat-wishlist").textContent = wishlist.length;
}

// ── Likes ─────────────────────────────────────────────────────────────────────
async function loadLikesTab() {
    const reactions = await fetch(`${API}/reactions/${username}`).then(r => r.json());
    const liked = reactions.filter(r => r.reaction === "LIKED");
    renderGames(liked, "profile-likes", game => `
        <button class="btn btn-ghost btn-sm" onclick="unlikeGame(${game.appid})">👎 Unlike</button>
        <button class="btn btn-ghost btn-sm" onclick="wishlistGame(${game.appid})">❤️</button>
    `);
}

async function unlikeGame(appid) {
    await fetch(`${API}/reactions/${appid}?username=${username}`, { method: "DELETE" });
    loadLikesTab();
    loadStats();
}

// ── Wishlist ──────────────────────────────────────────────────────────────────
async function loadWishlistTab() {
    const games = await fetch(`${API}/wishlist/${username}`).then(r => r.json());
    renderGames(games, "profile-wishlist", game => `
        <button class="btn btn-ghost btn-sm" onclick="removeWishlist(${game.appid})">🗑 Remove</button>
        <button class="btn btn-ghost btn-sm" onclick="likeGame(${game.appid})">👍</button>
    `);
}

async function removeWishlist(appid) {
    await fetch(`${API}/wishlist/${appid}?username=${username}`, { method: "DELETE" });
    loadWishlistTab();
    loadStats();
}

// ── Genres ────────────────────────────────────────────────────────────────────
async function loadGenresTab() {
    const genres = await fetch(`${API}/user/genres/${username}`).then(r => r.json());
    const div = document.getElementById("profile-genres");
    div.innerHTML = genres.length
        ? genres.map(g => `<span class="pill pill-accent">${g}</span>`).join("")
        : `<span class="pill">No genres selected</span>`;
}