async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    if (!username || !password) {
        alert("Please fill all fields");
        return;
    }

    try {

        const response = await fetch(
            "http://localhost:8000/api/login",
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

            localStorage.setItem(
                "username",
                data.username
            );

            alert("Login successful");

            window.location.href =
                "home.html";

        } else {

            alert(data.detail);
        }

    } catch (error) {

        console.error(error);
        alert("Cannot connect to server");
    }
}