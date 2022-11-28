const endpoint = document.getElementById('endpoint')
const gameDiv = document.getElementById('game');
const startButton = document.getElementById('start');

let gameApi = location.href.replace(/\/$/, "") + "/game";

endpoint.value = gameApi;

document.getElementById('endpointForm').addEventListener('submit', async function (e) {
    e.preventDefault(); // Stop form from submitting

    const response = await fetch(endpoint.value);

    const game = await response.json(); // Extract JSON from the HTTP response

    if (game.won) {
        return;
    }

    // Create guess form
    const form = document.createElement("form");
    const gameMessage = document.createElement("p");
    gameMessage.innerHTML = "Guess the number between " + game.min + " and " + game.max;
    form.appendChild(gameMessage);
    const attemptMessage = document.createElement("p");
    attemptMessage.innerHTML = "Attempt 1 "; // First attempt
    form.appendChild(attemptMessage);
    const guessInput = document.createElement("input");
    guessInput.type = "text";
    form.appendChild(guessInput);
    form.appendChild(document.createTextNode(" "));
    const guessSubmit = document.createElement("input");
    guessSubmit.type = "submit";
    guessSubmit.value = "Guess";
    form.appendChild(guessSubmit);
    const guessMessage = document.createElement("p");
    form.appendChild(guessMessage);
    gameDiv.innerHTML = "";
    gameDiv.appendChild(form);
    guessInput.focus()

    // Process guess
    form.addEventListener('submit', async function (e) {
        e.preventDefault(); // Stop form from submitting

        guessNumber = parseInt(guessInput.value);
        if (isNaN(guessNumber)) {
            guessMessage.innerHTML = "Please enter a number";
            return;
        }
        const guessEnpoint = endpoint.value + "/" + game.id + "/" + guessNumber;
        const response = await fetch(guessEnpoint);
        const guessGame = await response.json(); // Extract JSON from the HTTP response

        if (guessGame.won) {
            guessInput.disabled = true;
            guessSubmit.disabled = true;
            guessMessage.innerHTML = guessNumber + " is " + guessGame.message + " 👏";
            gameMessage.innerHTML = "You won";
            startButton.focus();
        } else {
            nextAttempt = parseInt(guessGame.attempts) + 1
            attemptMessage.innerHTML = "Attempt " + nextAttempt;
            guessMessage.innerHTML = guessNumber + " is " + guessGame.message;
        }
        guessInput.value = "";

    });
});

startButton.focus();