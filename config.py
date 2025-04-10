from operator import truediv
import redis
import redis.exceptions 


REDIS_HOST = 'localhost'
REDIS_PORT =  6379
REDIS_CLIENT = redis.Redis(host=REDIS_HOST , port=REDIS_PORT , decode_responses=True)


QUESTION_STREAM = 'quiz_questions'
ANSWER_STREAM = 'quiz_answers'
CONSUMER_GROUP = 'quiz_group'


OPENTDB_API_URL = "https://opentdb.com/api.php?amount=10&category=23&type=multiple"

#  khoi tao consumer group
def init_consumer_group():
    try:
        REDIS_CLIENT.xgroup_create(QUESTION_STREAM , CONSUMER_GROUP , id = '0' , mkstream=True)
        REDIS_CLIENT.xgroup_create(ANSWER_STREAM , CONSUMER_GROUP , id = '0' , mkstream= True)
    except redis.exceptions.ResponseError:
        #  kiem tra xem group da ton tai hay chua 
        
        pass 
    except redis.exceptions.ConnectionError as e :
        print(f'khong the ket noi  redis : {e}')
        raise
    
    