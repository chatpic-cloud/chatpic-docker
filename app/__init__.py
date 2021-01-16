from flask import Flask

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import UserManager
from flask_assets import Environment, Bundle
from flask_moment import Moment
from flaskext.markdown import Markdown
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from elasticsearch import Elasticsearch


sentry_sdk.init(
    dsn="https://e9122d47ca9b471e83fcee6e6afaaa12@o488855.ingest.sentry.io/5549957",
    integrations=[FlaskIntegration(transaction_style = "url")],
    traces_sample_rate=0.2,
)


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config.from_object(Config)
app.jinja_options['extensions'].append('jinja2.ext.do')
if app.config['DEBUG'] != 'False':
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)

Markdown(app)
mail = Mail(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["3000 per day", "20 per minute"]
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
assets = Environment(app)
moment = Moment(app)





css = Bundle('css/custom-footer.css','css/bootstrap.css','css/blog.css',
             'css/media.css',
            filters='cssmin', output='gen/packed.css')
assets.register('css_all', css)

js = Bundle('js/infiniscroll.js','js/delete.js','js/jquery.serialize-object.min.js',
            filters='jsmin', output='gen/packed.js')
assets.register('js_all', js)

from app import routes, models
user_manager = UserManager(app, db, models.User)

app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    if app.config['ELASTICSEARCH_URL'] else None