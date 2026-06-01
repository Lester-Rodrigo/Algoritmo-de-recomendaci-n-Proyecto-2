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