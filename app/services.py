import hashlib, requests
from app import db
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from app import app
import os
import time
import base64
import calendar
import requests
from .models import Media, Comment, CreditTransaction, Role



# form.data['media'],form.data['thumbnail'],form.data['title'],form.data['uploader'],form.data['cp_id']

# sign url to nginx secure link

def assign_role_to_user(role_name, user):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role)
        role.name = role_name
        db.session.add(role)
        print(f'new {role.name}')
    print(f'assign {role}')
    print(f'name = {role_name}')
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()


def modify_credit_balance(user, amount, description):
    user.credits += amount
    trans = CreditTransaction(amount=amount,
                              description=description,
                              user_id=user.id)
    db.session.add(trans)
    db.session.add(user)
    db.session.commit()


def check_ip(ip):
    response = requests.get(f'http://check.getipintel.net/check.php?ip={ip}&contact=admin@chatpic.exposed&flags=m')
    print(f'voting ip check result = {response.text}')
    if response.text == "1":
        print(f'voting ip check result = nope')
        return False
    else:
        print(f'voting ip check result = ok')
        return True


def sign_url(url, expire, secret):
    future = datetime.utcnow() + timedelta(seconds=expire)
    expiry = calendar.timegm(future.timetuple())
    secure_link = f"{secret}{url}{expiry}".encode('utf-8')
    print(str(secure_link))
    hash = hashlib.md5(secure_link).digest()
    base64_hash = base64.urlsafe_b64encode(hash)
    str_hash = base64_hash.decode('utf-8').rstrip('=')
    print(f"https://media.chatpic.exposed{url}?st={str_hash}&e={expiry}")
    return str_hash, expiry


def extended_mail_validation(mail):
    url = "https://chatpic-mail-check.herokuapp.com/"
    payload = {"to_emails": [mail], "from_email": "mail-validation@chatpic.exposed", 'hello_name': 'mx.chatpic.exposed'}
    response = requests.post(url, json=payload)
    print(response.text)
    try:
        if response.json()[0]['is_reachable'] == 'safe':
            return True
        if response.json()[0]['misc']['is_disposable'] or response.json()[0]['is_reachable'] == 'invalid':
            return False
        if response.json()[0]['is_reachable'] == 'unknown' and response.json()[0]['mx']['accepts_mail']:
            return True
    except Exception as e:
        return False


def delete_media(filename, thumbnail):
    file_storage_location = app.config['FILE_STORAGE_LOCATION']
    file = os.path.basename(filename)
    thumb = os.path.basename(thumbnail)
    try:
        os.remove(f"{file_storage_location}{file}")
        os.remove(f"{file_storage_location}{thumb}")
        return True
    except:
        return False


def save_new_image(media_in, thumbnail, title, uploader, cp_id):
    md5 = hashlib.md5(media_in.read()).hexdigest()
    media = Media.query.filter_by(md5=md5).first()
    if not media:
        new_media = Media(md5=md5, title=title, thumbnail=thumbnail.filename, filename=media_in.filename,
                          upload_time=datetime.utcnow(), hidden=False, uploader=uploader, cp_id=cp_id)

        file_storage_location = app.config['FILE_STORAGE_LOCATION']
        if not os.path.exists(file_storage_location):
            os.makedirs(file_storage_location)

        try:
            media_in.seek(0)
            media_in.save(f'{file_storage_location}{media_in.filename}')
            thumbnail.seek(0)
            thumbnail.save(f'{file_storage_location}{thumbnail.filename}')
        except Exception:
            response_object = {
                "status": "failed",
                "message": "Image could not be saved",
            }
            return response_object, 500
        response_object = {
            "status": "success",
            "message": "Image accpeted",
            "md5": new_media.md5,
        }
        save_changes(new_media)

        return response_object, 201

    else:
        media.reuploads += 1
        media.upload_time = datetime.utcnow()
        media.cp_id = cp_id
        if not media.uploader:
            media.uploader = uploader

        if title != media.title and title != "":
            comment = Comment(media_id=media.md5, content=title, name=uploader)
            save_changes(comment)

        save_changes(media)

        response_object = {
            "status": "success",
            "message": "Image already exists, increasing reupload count",
        }
        return response_object, 200


def save_changes(data):
    db.session.add(data)
    db.session.commit()

