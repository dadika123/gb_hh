from environs import Env

env = Env()
env.read_env()


SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
DB_ENGINE = env('DB_ENGINE')
DB_HOST = env('POSTGRES_HOST')
DB_PORT = env('POSTGRES_PORT')
DB_NAME = env('POSTGRES_DB')
DB_LOGIN = env('POSTGRES_USER')
DB_PASS = env('POSTGRES_PASSWORD')
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
