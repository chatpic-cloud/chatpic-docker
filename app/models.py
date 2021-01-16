from app import db
from flask_user import UserMixin
from datetime import datetime
from sqlalchemy_fulltext import FullText, FullTextSearch
from sqlalchemy.ext.declarative import declarative_base
from app.search import add_to_index, remove_from_index, query_index


import uuid
Base = declarative_base()
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.md5.in_(ids)).order_by(
            db.case(when, value=cls.md5)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

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

class Media(FullText,db.Model, SearchableMixin):
    __tablename_ = 'media'
    __fulltext_columns__ = ('filename','title')
    __msearch_primary_key__ = 'md5'
    __searchable__ = ['title','filename']

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
    girl = db.relationship('Girl', backref='girl', lazy='joined')
    girl_id = db.Column(db.Integer, db.ForeignKey('girl.id'))




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

class Country(db.Model):
    __tablename_ = 'country'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    short_code = db.Column(db.String(3), nullable=True, default="")
    name = db.Column(db.String(128), nullable=True, default="")

class Links(db.Model):
    __tablename_ = 'links'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(512), nullable=False, default="")
    girl_id = db.Column(db.Integer, db.ForeignKey('girl.id'))



class Girl(db.Model, SearchableMixin):
    __searchable__ = ['first_name','last_name']
    __tablename_ = 'girl'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country = db.relationship('Country', backref='country', lazy='joined')
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    first_name = db.Column(db.String(128), nullable=True, default="")
    last_name = db.Column(db.String(128), nullable=True, default="")
    phone = db.Column(db.String(128), nullable=True, default="")
    email = db.Column(db.String(128), nullable=True, default="")
    address = db.Column(db.String(512), nullable=True, default="")
    dob = db.Column(db.Date)
    links = db.relationship('Links', backref='link', lazy='joined')
    media = db.relationship("Media", backref='girl_media')




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



db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)

