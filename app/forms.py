from flask_wtf import FlaskForm,RecaptchaField
from wtforms import StringField, TextAreaField, BooleanField, SubmitField,HiddenField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileField,FileAllowed, FileRequired
from werkzeug.utils import secure_filename


class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    title = StringField('Title',validators=[DataRequired()])
    submit = SubmitField('Post')

class VoteForm(FlaskForm):
    md5 = StringField('id',validators=[DataRequired()])
    vote = StringField('up or down',validators=[DataRequired()])

class CommentForm(FlaskForm):
    content = StringField('Comment content',validators=[DataRequired()])
    media_id = HiddenField('Media ID',validators=[DataRequired()])
    name = StringField('Display Name')
    #recaptcha = RecaptchaField()

class ReportForm(FlaskForm):
    md5 = StringField('Comment content',validators=[DataRequired()])
    reason = HiddenField('Media ID',validators=[DataRequired()])
    comment = StringField('Display Name')
    email = StringField('Email address')

    #recaptcha = RecaptchaField()

class UploadForm(FlaskForm):
    media = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png','jpeg','mp4'], 'Images only!')
    ])
    thumbnail = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png','jpeg'], 'Images only!')
    ])
    #filename = StringField('Filename',validators=[DataRequired()])
    title = StringField('Title')
    uploader = StringField('Uploader')
    cp_id = StringField('Chatpic ID')

