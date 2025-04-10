from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room
import threading
import time
import html
from config import init_consumer_group, REDIS_CLIENT , QUESTION_STREAM , ANSWER_STREAM
from event_system import QuizEventSystem
from worker import run_worker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
quiz_system = QuizEventSystem(socketio)

player_questions = {}
player_current_index = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    player_id = data['player_id']
    join_room(player_id)
    print(f"[Backend] {player_id} joined")
    
    questions = quiz_system.fetch_random_questions()
    if not questions:
        print("[Backend] Failed to fetch questions from OpenTDB")
        socketio.emit('error', {'message': 'Failed to load questions'}, room=player_id)
        return
    
    for q in questions:
        q['question'] = html.unescape(q['question'])
        q['correct_answer'] = html.unescape(q['correct_answer'])
        q['incorrect_answers'] = [html.unescape(ans) for ans in q['incorrect_answers']]
    
    player_questions[player_id] = questions
    player_current_index[player_id] = 0
    print(f"[Backend] Loaded {len(questions)} questions for {player_id}")
    send_next_question(player_id)

@socketio.on('submit_answer')
def on_submit_answer(data):
    player_id = data['player_id']
    question_id = data['question_id']
    answer = data['answer'] or ""  # Xử lý answer rỗng
    question_data = {
        'question_id': question_id,
        'answer': data['correct_answer'],
        'points': '10'
    }
    print(f"[Backend] {player_id} submitted answer for {question_id}: {answer}")
    quiz_system.submit_answer(player_id, question_data, answer)
    send_next_question(player_id)

def send_next_question(player_id):
    if player_id in player_questions:
        questions = player_questions[player_id]
        current_index = player_current_index[player_id]
        
        if current_index < len(questions):
            question_data = {
                'question_id': f"{player_id}_q{current_index + 1}",
                'question': questions[current_index]['question'],
                'correct_answer': questions[current_index]['correct_answer'],
                'incorrect_answers': questions[current_index]['incorrect_answers']
            }
            quiz_system.send_question(question_data, player_id)
            player_current_index[player_id] += 1
        else:
            print(f"[Backend] {player_id} finished all questions")
            score = quiz_system.redis.hget('player_scores', player_id) or 0
            socketio.emit('game_over', {
                'message': 'Quiz finished!',
                'score': int(score),
                'player_id': player_id
            }, room=player_id)
            quiz_system.update_leaderboard()

def reset_redis_data():
    try:
        REDIS_CLIENT.delete('player_scores')
        REDIS_CLIENT.delete('leaderboard')
        REDIS_CLIENT.delete(QUESTION_STREAM)
        REDIS_CLIENT.delete(ANSWER_STREAM)
        print("[Backend] Cleared Redis data")
    except Exception as e:
        print(f"[Backend] Error clearing Redis data: {e}")

def run_app():
    reset_redis_data()
    init_consumer_group()
    worker_thread = threading.Thread(target=run_worker, args=(1,))
    worker_thread.start()
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    run_app()