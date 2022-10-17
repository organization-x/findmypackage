addEventListener('DOMContentLoaded', (event) => {
    let form = document.getElementById("track_form");
    let submitButton = document.getElementById("submit_button");
    submitButton.disabled = false;
    form.addEventListener('submit', (event) => {
        submitButton.disabled = true;
    })
})