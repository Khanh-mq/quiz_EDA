import time
from event_system import QuizEventSystem

def run_server():
    quiz_system = QuizEventSystem()
    questions = quiz_system.fetc_random_questions()  # Lấy 3 câu hỏi ngẫu nhiên
    for idx, q in enumerate(questions):
        question_data = {
            'question_id': f"q{idx+1}",
            'question': q['question'],
            'correct_answer': q['correct_answer']
        }
        quiz_system.send_question(question_data)
        time.sleep(2)  # Đợi 2 giây giữa các câu hỏi
    print("[Server] Quiz finished!")