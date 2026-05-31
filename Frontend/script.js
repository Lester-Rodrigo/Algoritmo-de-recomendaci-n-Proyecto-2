function login(){

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    if(email === "" || password === ""){

        alert("Please fill all fields");
        return;
    }

    console.log("Email:", email);
    console.log("Password:", password);

    alert("Login button works!");
}

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

    alert("Account created successfully!");
}