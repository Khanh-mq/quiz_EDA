const socket = io();
let playerId = null;
let currentQuestion = null;
let timer = null;

function joinGame() {
    playerId = document.getElementById('player_id').value.trim();
    if (!playerId) {
        alert('Please enter a player ID');
        return;
    }
    console.log(`[Frontend] Joining game with ID: ${playerId}`);
    socket.emit('join', { player_id: playerId });
    document.getElementById('player_id').disabled = true;
}

socket.on('connect', () => {
    console.log('[Frontend] Connected to SocketIO server');
});

socket.on('error', (data) => {
    console.log('[Frontend] Error:', data.message);
    alert(data.message);
});

socket.on('new_question', (data) => {
    if (data.player_id === playerId) {
        console.log(`[Frontend] Received question: ${data.question}`);
        currentQuestion = data;
        document.getElementById('question_text').innerText = data.question;
        
        const answersDiv = document.getElementById('answers');
        answersDiv.innerHTML = '';
        data.answers.forEach(answer => {
            const button = document.createElement('button');
            button.className = 'answer-btn';
            button.innerText = answer;
            button.onclick = () => submitAnswer(answer);
            answersDiv.appendChild(button);
        });
        
        document.getElementById('question').style.display = 'block';
        document.getElementById('result').innerText = '';
        startTimer(30);
    }
});

function submitAnswer(answer) {
    if (currentQuestion) {
        // Nếu answer là null (hết thời gian), gửi chuỗi rỗng
        const selectedAnswer = answer || "";
        console.log(`[Frontend] Submitting answer: ${selectedAnswer}`);
        socket.emit('submit_answer', {
            player_id: playerId,
            question_id: currentQuestion.question_id,
            answer: selectedAnswer,
            correct_answer: currentQuestion.answer
        });
        clearInterval(timer);
        document.getElementById('timer').innerText = 'Time left: Waiting...';
    }
}

socket.on('answer_result', (data) => {
    if (data.player_id === playerId) {
        document.getElementById('result').innerText = data.correct ? 'Correct!' : 'Wrong!';
        document.getElementById('question').style.display = 'none';
    }
});

socket.on('leaderboard_update', (data) => {
    const leaderboard = document.getElementById('leaderboard');
    leaderboard.innerHTML = '';
    data.leaderboard.forEach(([player, score]) => {
        const li = document.createElement('li');
        li.innerText = `${player}: ${score} points`;
        leaderboard.appendChild(li);
    });
});

socket.on('game_over', (data) => {
    if (data.player_id === playerId) {
        document.getElementById('result').innerText = `${data.message} Your final score: ${data.score} points`;
        document.getElementById('question').style.display = 'none';
    }
});

function startTimer(seconds) {
    let timeLeft = seconds;
    document.getElementById('timer').innerText = `Time left: ${timeLeft}s`;
    timer = setInterval(() => {
        timeLeft--;
        document.getElementById('timer').innerText = `Time left: ${timeLeft}s`;
        if (timeLeft <= 0) {
            clearInterval(timer);
            submitAnswer(null); // Gửi null nếu hết giờ
        }
    }, 1000);
}