

const avatar = document.getElementById("avatar");
const banner = document.getElementById("banner");

const avatarUpload = document.getElementById("avatarUpload");
const bannerUpload = document.getElementById("bannerUpload");

/* Abrir selector al hacer click */

avatar.addEventListener("click", () => {
    avatarUpload.click();
});

banner.addEventListener("click", () => {
    bannerUpload.click();
});

/* Cambiar avatar */

avatarUpload.addEventListener("change", function(){

    const file = this.files[0];

    if(!file) return;

    const reader = new FileReader();

    reader.onload = function(e){
        avatar.src = e.target.result;
    };

    reader.readAsDataURL(file);

});

/* Cambiar banner */

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

genres.forEach(btn => {

    btn.addEventListener("click", () => {

        console.log("CLICK");

        btn.classList.toggle("selected");

    });

});

function goNextPage(){

    window.location.href =
    "/static/html/profile.html";

}

