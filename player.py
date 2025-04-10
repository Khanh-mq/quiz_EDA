import random
from event_system import QuizEventSystem

def player_callback(player_id, question_data):
    quiz_system = QuizEventSystem()
    is_correct = random.choice([True, False])
    answer = question_data['answer'] if is_correct else "WrongAnswer"
    quiz_system.submit_answer(player_id, question_data, answer)

def run_player(player_id):
    quiz_system = QuizEventSystem()
    consumer_name = f"player_{player_id}"
    quiz_system.read_questions(player_id, consumer_name, player_callback)