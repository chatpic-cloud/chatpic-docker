import os,logging
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_EMAIL_SENDER_EMAIL = "notifications@chatpic.exposed"
    USER_ENABLE_CONFIRM_EMAIL = True
    USER_APP_NAME = "chatpic.exposed - The chatpic archive"
    USER_ENABLE_EMAIL = True


    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'mail.postale.io'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'notifications@chatpic.exposed'
    MAIL_PASSWORD = '2Xr74jAWc6'
    MAIL_DEFAULT_SENDER = 'chatpic.exposed <notifications@chatpic.exposed>'
    MAIL_DEBUG = 1




    # Flask-User settings
    USER_ENABLE_USERNAME = True    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "notifications@chatpic.exposed"

    POSTS_PER_PAGE = 25
    FILE_STORAGE_LOCATION = os.environ.get('FILE_STORAGE_LOCATION') or "./app/static/uploads/"
    CDN_URL = os.environ.get('CDN_URL') or "https://media.chatpic.exposed/"
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY') or "invalid"
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY') or "invalid"
    DEBUG = os.environ.get('DEBUG') or True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    RATELIMIT_STORAGE_URL = os.environ.get('STORAGE_URL') or "memory://"
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or "filesystem"
    CACHE_DIR = os.environ.get('CACHE_DIR') or "./cache/"

    CAPTCHA_ENABLE = True
    CAPTCHA_LENGTH = 5
    CAPTCHA_WIDTH = 160
    CAPTCHA_HEIGHT = 60
    SESSION_TYPE = 'sqlalchemy'


    ELASTICSEARCH = {"hosts": ["g3eg25dy8o:ezhe6qhw59@test-648873209.eu-west-1.bonsaisearch.net:443"]}
