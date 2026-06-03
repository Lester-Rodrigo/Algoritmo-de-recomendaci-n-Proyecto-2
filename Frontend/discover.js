const API =
    "http://localhost:8000/api";

const username =
    localStorage.getItem("username");

window.onload = async () => {

    await loadRecommended();

    await loadWishlistRecommendations();

    await loadSimilarUserRecommendations();
};
async function loadRecommended(){

    const response =
        await fetch(
            `${API}/recommendations/preferences/${username}`
        );

    const games =
        await response.json();

    renderGames(
        games,
        "recommended"
    );
}
async function loadWishlistRecommendations(){

    const response =
        await fetch(
            `${API}/recommendations/wishlist/${username}`
        );

    const games =
        await response.json();

    renderGames(
        games,
        "wishlistBased"
    );
}
async function loadSimilarUserRecommendations(){

    const response =
        await fetch(
            `${API}/recommendations/similar-users/${username}`
        );

    const games =
        await response.json();

    renderGames(
        games,
        "similarUsers"
    );
}
function renderGames(
    games,
    containerId
){

    const container =
        document.getElementById(
            containerId
        );

    container.innerHTML = "";

    games.forEach(game => {

        container.innerHTML += `

        <div class="game-card">

            <h3>${game.name}</h3>

            <p>
                Score: ${game.score}
            </p>

            <div class="actions">

                <button
                    onclick="addLibrary(${game.appid})">

                    Biblioteca

                </button>

                <button
                    onclick="addWishlist(${game.appid})">

                    Wishlist

                </button>

            </div>

        </div>
        `;
    });
}
async function addLibrary(appid){

    await fetch(
        `${API}/library/add`,
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username,
                appid
            })
        }
    );
}
async function addWishlist(appid){

    await fetch(
        `${API}/wishlist/add`,
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username,
                appid
            })
        }
    );
}