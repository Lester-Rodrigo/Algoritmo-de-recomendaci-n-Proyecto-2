console.log("GENRES CARGADO");
function register(){

    const username =
        document.getElementById("username").value;

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if(
        username === "" ||
        email === "" ||
        password === "" ||
        confirmPassword === ""
    ){
        alert("Please complete all fields");
        return;
    }

    if(password !== confirmPassword){
        alert("Passwords do not match");
        return;
    }

    window.location.href =
        "selectgenre.html";
}