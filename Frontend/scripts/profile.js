const avatar = document.getElementById("avatar");
const banner = document.getElementById("banner");

const avatarUpload =
    document.getElementById("avatarUpload");

const bannerUpload =
    document.getElementById("bannerUpload");

avatar.addEventListener("click", () => {
    avatarUpload.click();
});

banner.addEventListener("click", () => {
    bannerUpload.click();
});

avatarUpload.addEventListener("change", function(){

    const file = this.files[0];

    if(!file) return;

    const reader = new FileReader();

    reader.onload = function(e){
        avatar.src = e.target.result;
    };

    reader.readAsDataURL(file);

});

bannerUpload.addEventListener("change", function(){

    const file = this.files[0];

    if(!file) return;

    const reader = new FileReader();

    reader.onload = function(e){

        banner.style.backgroundImage =
            `url(${e.target.result})`;

        banner.style.backgroundSize = "cover";
        banner.style.backgroundPosition = "center";

    };

    reader.readAsDataURL(file);

});

const games =
    JSON.parse(
        localStorage.getItem(
            "recommendedGames"
        )
    );

if (games) {

    const container =
        document.getElementById(
            "games-container"
        );

    games.forEach(game => {

        const card =
            document.createElement("div");

        card.classList.add(
            "game-card"
        );

        const imageUrl =
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${game.appid}/header.jpg`;

        card.innerHTML = `
            <img
                src="${imageUrl}"
                alt="${game.game}"
                class="game-image"
            >

            <h4>${game.game}</h4>

            <p>Match Score: ${game.score}</p>

            <p>$${game.price}</p>
        `;

        container.appendChild(card);

    });
}