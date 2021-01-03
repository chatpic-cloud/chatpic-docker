from app import app as application
from app import db,user_manager
#from app.models import User, Post

@application.shell_context_processor
def make_shell_context():
    return {'db': db,'user_manager':user_manager}

if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
