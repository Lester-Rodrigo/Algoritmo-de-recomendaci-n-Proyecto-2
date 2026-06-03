// Load genres from the graph on page load
window.onload = async () => {
    const res    = await fetch("/api/genres");
    const genres = await res.json();
    const grid   = document.getElementById("genre-grid");

    genres.forEach(genre => {
        const btn = document.createElement("button");
        btn.className   = "genre-btn";
        btn.textContent = genre;
        btn.addEventListener("click", () => btn.classList.toggle("selected"));
        grid.appendChild(btn);
    });
};

async function goNextPage() {
    const selectedButtons = document.querySelectorAll(".genre-btn.selected");

    if (selectedButtons.length < 3) {
        alert("Please select at least 3 genres.");
        return;
    }

    const genres   = Array.from(selectedButtons).map(btn => btn.textContent.trim());
    const username = localStorage.getItem("username");

    try {
        await fetch("/api/user/genres", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, genres })
        });

        window.location.href = "/static/html/home.html";

    } catch (error) {
        console.error(error);
        alert("Error saving genres");
    }
}