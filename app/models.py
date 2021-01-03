from app import db
from flask_user import UserMixin
from datetime import datetime
from sqlalchemy_fulltext import FullText, FullTextSearch
import uuid

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    # User Authentication fields
    email = db.Column(db.String(255), nullable=True, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary='user_roles')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    credits = db.Column(db.Integer, default=0)
    all_time_credits = db.Column(db.Integer)
    credit_transactions = db.relationship('CreditTransaction', backref='credit_transactions', lazy='dynamic')



    # User fields
    active = db.Column(db.Boolean())

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class Post(db.Model):
    __tablename_ = 'posts'
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.Text(), default='')
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    content = db.Column(db.Text(), default='')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Media(FullText,db.Model):
    __tablename_ = 'media'
    __fulltext_columns__ = ('filename','title')
    __msearch_primary_key__ = 'md5'
    md5 = db.Column(db.String(32), primary_key=True, autoincrement=False)
    filename = db.Column(db.String(255), unique=False, nullable=False)
    thumbnail = db.Column(db.String(255), unique=False, nullable=False,default='not_available.jpg')
    title = db.Column(db.String(255), unique=False, nullable=True, default="")
    reuploads = db.Column(db.Integer, nullable=False, default=0)
    votes = db.Column(db.Integer, nullable=False, default=0)
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reported = db.Column(db.Boolean, nullable=False, default=False)
    hidden = db.Column(db.Boolean, default=False)
    uploader = db.Column(db.String(255))
    cp_id = db.Column(db.String(32))
    comments = db.relationship('Comment', backref='comment', lazy='dynamic', cascade="all, delete, delete-orphan" )
    comment_count = db.Column(db.Integer, nullable=True, default=0)
    views = db.Column(db.Integer, nullable=True, default=0)
    reports = db.relationship('Report', backref='report', lazy='dynamic', cascade="all, delete, delete-orphan" )


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer(), primary_key=True)
    content = db.Column(db.Text())
    media_id = db.Column(db.String(32), db.ForeignKey('media.md5'))
    time = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(64), default='anon')


class Vote(db.Model):
    __tablename_ = 'votes'
    id = db.Column(db.Integer(), primary_key=True)
    ip = db.Column(db.String(15),nullable=False)
    media_id = db.Column(db.String(32), db.ForeignKey('media.md5'))
    time = db.Column(db.DateTime, default=datetime.utcnow)

class View(db.Model):
    __tablename_ = 'views'
    id = db.Column(db.Integer(), primary_key=True)
    ip = db.Column(db.String(64),nullable=False)
    media_id = db.Column(db.String(32), db.ForeignKey('media.md5'))
    time = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename_ = 'reports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    media_md5 = db.Column(db.String(32), db.ForeignKey('media.md5'))
    reason = db.Column(db.String(128), nullable=True, default="")
    comment = db.Column(db.String(512), nullable=True, default="")
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    email = db.Column(db.String(512), nullable=True, default="")
    ip = db.Column(db.String(32), nullable=False)
    reported_by = db.Column(db.String(50), nullable=True, unique=False)
    media = db.relationship('Media', backref='media', lazy='joined')
    status = db.Column(db.String(10), nullable=False)



class Order(db.Model):
    __tablename_ = 'orders'
    id = db.Column(db.String(128), primary_key=True)
    status = db.Column(db.String(512), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.Column(db.String(512), nullable=False, default="")
    email = db.Column(db.String(512), nullable=False, default="")

class CreditTransaction(db.Model):
        __tablename_ = 'credit_transaction'
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        amount = db.Column(db.Integer)
        description = db.Column(db.String(512))
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# oZmMZjNrajyq