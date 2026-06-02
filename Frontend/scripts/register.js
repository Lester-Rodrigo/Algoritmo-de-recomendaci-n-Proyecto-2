console.log("GENRES CARGADO");
async function register(){

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

    const emailRegex =
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if(!emailRegex.test(email)){
    alert("Please enter a valid email.");
    return;
    }

    if(password !== confirmPassword){
        alert("Passwords do not match");
        return;
    }

    try {

        const response = await fetch(
            "/api/register",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            alert("Account created");

            localStorage.setItem(
                "username",
                data.username
            );

            window.location.href =
                "/static/html/selectgenre.html";

        } else {

            alert(data.detail);
        }

    } catch (error) {

        console.error(error);
        alert("Cannot connect to server");
    }
}