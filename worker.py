from event_system import QuizEventSystem

def run_worker(worker_id):
    quiz_system = QuizEventSystem()
    quiz_system.process_answers(worker_id)