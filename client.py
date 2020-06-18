import redis
import random


redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, db=3)   # host是redis主机，需要redis服务端和客户端都启动 redis默认端口是6379


