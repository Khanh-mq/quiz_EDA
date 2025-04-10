import time
import requests
import html
import random
import json
from config import REDIS_CLIENT, QUESTION_STREAM, ANSWER_STREAM, CONSUMER_GROUP, OPENTDB_API_URL

class QuizEventSystem:
    def __init__(self, socketio=None):
        self.redis = REDIS_CLIENT
        self.socketio = socketio

    def fetch_random_questions(self, amount=3):
        try:
            response = requests.get(OPENTDB_API_URL)
            response.raise_for_status()
            data = response.json()
            if data['response_code'] == 0:
                print(f"[EventSystem] Fetched {len(data['results'])} questions from OpenTDB")
                return data['results']
            else:
                print(f"[EventSystem] OpenTDB response code: {data['response_code']}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"[EventSystem] Failed to fetch questions: {e}")
            return []

    def send_question(self, question_data, player_id):
        question_data['question'] = html.unescape(question_data['question'])
        question_data['correct_answer'] = html.unescape(question_data['correct_answer'])
        
        incorrect_answers = question_data.get('incorrect_answers', [])
        incorrect_answers = [html.unescape(ans) for ans in incorrect_answers]
        
        all_answers = incorrect_answers + [question_data['correct_answer']]
        random.shuffle(all_answers)
        
        event_for_redis = {
            'type': 'question',
            'question_id': question_data['question_id'],
            'question': question_data['question'],
            'answer': question_data['correct_answer'],
            'answers': json.dumps(all_answers),
            'points': '10',
            'timestamp': str(int(time.time() * 1000)),
            'player_id': player_id
        }
        self.redis.xadd(QUESTION_STREAM, event_for_redis)
        
        event_for_socketio = {
            'type': 'question',
            'question_id': question_data['question_id'],
            'question': question_data['question'],
            'answer': question_data['correct_answer'],
            'answers': all_answers,
            'points': '10',
            'timestamp': str(int(time.time() * 1000)),
            'player_id': player_id
        }
        if self.socketio:
            print(f"[EventSystem] Emitting question to {player_id}")
            self.socketio.emit('new_question', event_for_socketio, room=player_id)
        print(f"[Server] Sent question to {player_id}: {question_data['question']}")

    def submit_answer(self, player_id, question_data, answer):
        # Xử lý trường hợp answer là null hoặc rỗng
        answer = answer or ""
        event = {
            'type': 'answer',
            'player_id': player_id,
            'question_id': question_data['question_id'],
            'answer': answer,
            'correct_answer': question_data['answer'],
            'points': question_data['points'],
            'timestamp': str(int(time.time() * 1000))
        }
        self.redis.xadd(ANSWER_STREAM, event)
        print(f"[Player {player_id}] Submitted answer: {answer}")

    def process_answers(self, worker_id):
        while True:
            try:
                messages = self.redis.xreadgroup(
                    CONSUMER_GROUP, f"worker_{worker_id}", {ANSWER_STREAM: '>'}, count=1, block=1000
                )
                for stream, entries in messages:
                    for entry_id, data in entries:
                        player_id = data['player_id']
                        answer = data['answer'] or ""  # Xử lý answer rỗng
                        correct_answer = data['correct_answer']
                        points = int(data['points'])

                        result = {'player_id': player_id, 'correct': False}
                        if answer.lower() == correct_answer.lower():
                            self.redis.hincrby('player_scores', player_id, points)
                            score = self.redis.hget('player_scores', player_id)
                            self.redis.zadd('leaderboard', {player_id: int(score)})
                            result['correct'] = True
                            print(f"[Worker {worker_id}] {player_id} answered correctly (+{points} points)")
                        else:
                            print(f"[Worker {worker_id}] {player_id} answered incorrectly")

                        if self.socketio:
                            self.socketio.emit('answer_result', result, room=player_id)
                            self.update_leaderboard()

                        self.redis.xack(ANSWER_STREAM, CONSUMER_GROUP, entry_id)
            except Exception as e:
                print(f"[Worker {worker_id}] Error: {e}")
                time.sleep(1)

    def update_leaderboard(self):
        leaderboard = self.redis.zrange('leaderboard', 0, -1, withscores=True, desc=True)
        if self.socketio:
            print("[EventSystem] Updating leaderboard")
            self.socketio.emit('leaderboard_update', {'leaderboard': [(p, float(s)) for p, s in leaderboard]})