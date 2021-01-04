from app import app
from flask import render_template, redirect, url_for, flash, request, make_response, Markup
from .forms import PostForm, UploadForm, VoteForm, CommentForm, ReportForm
from .models import Post, Media, Vote, View, Comment, Report, Order, User, CreditTransaction, Role
from .services import save_new_image, save_changes, delete_media, extended_mail_validation, sign_url, check_ip, modify_credit_balance, assign_role_to_user
from app import db, limiter, mail
from flask_user import roles_required, current_user, user_manager,login_required
from datetime import datetime, timedelta
import sqlalchemy_fulltext.modes as FullTextMode
from sqlalchemy_fulltext import FullText, FullTextSearch
from flask_mail import Message

from coinbase_commerce.error import WebhookInvalidPayload, SignatureVerificationError
from coinbase_commerce.webhook import Webhook



@app.route("/search")
@limiter.limit("6 per minute")
def w_search():
    keyword = request.args.get('keyword')
    if keyword.startswith('anon'):
        return redirect(url_for('user_media', username=keyword))
    page = request.args.get('page', 1, type=int)
    results = db.session.query(Media).filter(FullTextSearch(keyword, Media, FullTextMode.NATURAL)).filter_by(reported=False,hidden=False).paginate(
        page, app.config['POSTS_PER_PAGE'], True)
    return render_template('media_overview.html', media=results,keyword=keyword)

@app.route('/')
def index():
    #role = Role(name='admin')
    #current_user.roles=[role,]
    #db.session.commit()
    page = request.args.get('page', 1, type=int)
    # posts = [{"title":"Test","date":datetime.utcnow(),"content":"Example content"},{"title":"Test2","date":datetime.utcnow(),"content":"Nulla quos animi officia tempora. Beatae officia doloribus nihil ut aut reprehenderit. Et ratione praesentium perspiciatis rerum voluptatibus quia. Recusandae iure beatae repellat architecto."},{"title":"Test3","date":datetime.utcnow(),"content":"Example content"}]
    posts = Post.query.order_by(Post.date.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], True)

    return render_template('posts.html', posts=posts)


@app.route('/admin')
@roles_required('admin')
def admin_overview():
    return render_template('admin_overview.html')


@app.route('/admin/posts/<id>', methods=['GET', 'POST', 'DELETE'])
@roles_required('admin')
def admin_edit_posts(id):
    form = PostForm()
    post = Post.query.filter_by(id=id).first_or_404()
    if form.validate_on_submit():
        post.content = form.data['content']
        post.title = form.data['title']
        db.session.add(post)
        db.session.commit()
        flash('Your post has been changed!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    elif request.method == 'DELETE':
        db.session.delete(post)
        db.session.commit()
    return render_template('posts_admin.html', title='Admin Posts',
                           form=form, post=post)


@app.route('/admin/posts/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_posts():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(content=form.data['content'], author=current_user,
                    title=form.data['title'])
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    return render_template('posts_admin.html', title='Admin Posts',
                           form=form)

@app.route('/loaderio-79359c48ba3b00ed42a191c546326da0/')
def verify():
    return 'loaderio-79359c48ba3b00ed42a191c546326da0'

@app.route('/media/')
def all_media():
    page = request.args.get('page', 1, type=int)
    order_by = request.args.get('order_by', 'time', type=str)
    if not current_user.is_anonymous and current_user.has_roles('realtime_access'):
        if page == 1 or not request.cookies.get('startTime'):
            start_time = datetime.utcnow()
        else:
            start_time = request.cookies.get('startTime')
    else:
        # for now, make start time static
        start_time = datetime.utcnow().replace(microsecond=0, second=0, minute=0)

    if order_by == 'votes':
        media = Media.query.filter(Media.hidden==False, Media.reported==False, Media.votes != 0).order_by(Media.votes.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    elif order_by == 'views':
        media = Media.query.filter_by(hidden=False, reported=False).order_by(Media.views.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    elif order_by == 'reuploads':
        media = Media.query.filter_by(hidden=False, reported=False).order_by(Media.reuploads.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    elif order_by == 'comments':
        media = Media.query.filter_by(hidden=False, reported=False).order_by(Media.comment_count.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    else:
        media = Media.query.filter(Media.upload_time <= start_time).filter_by(hidden=False, reported=False).order_by(
            Media.upload_time.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    response = make_response(render_template('media_overview.html', media=media,order_by=order_by))
    if page == 1:
        response.set_cookie('startTime', str(datetime.utcnow()))
    return response




@app.route('/user/<username>')
@limiter.limit("6 per minute")
def user_media(username):
    page = request.args.get('page', 1, type=int)
    media = Media.query.filter_by(hidden=False, reported=False, uploader=username).paginate(
        page, app.config['POSTS_PER_PAGE'], True)
    return render_template('media_overview.html', media=media, username=username)


@app.route('/media/<md5>')
def show_media(md5):
    form = CommentForm()
    report_form = ReportForm()
    media = Media.query.filter_by(md5=md5, hidden=False).first_or_404()
    view = View.query.filter_by(media_id=media.md5, ip=request.remote_addr).order_by(View.time.desc()).first()
    if not view or datetime.utcnow() > (view.time + timedelta(hours=24)):
        view = View(ip=request.remote_addr, media_id=media.md5)
        media.views += 1
        save_changes(media)
        save_changes(view)

    report_email = request.cookies.get('report_mail')

    return render_template('media.html', med=media,form=form, report_form=report_form, report_email=report_email)


@app.route('/media/upload', methods=['POST'])
@limiter.exempt
def upload_file():
    form = UploadForm(meta={"csrf": False})
    if form.validate_on_submit():
        return save_new_image(form.data['media'], form.data['thumbnail'], form.data['title'], form.data['uploader'],
                              form.data['cp_id'])
    return {"msg": "file not valid"}

@app.route('/comment', methods=['POST'])
@limiter.limit("1 per minute")
def comment_file():
    form = CommentForm()
    if form.validate_on_submit():
        media = Media.query.get(form.data['media_id'])
        if media:
            comment = Comment(media_id=form.data['media_id'], content=form.data['content'],name=form.data['name'])
            save_changes(comment)
            media.comment_count +=1
            save_changes(media)
            flash('Successfully posted comment')
    else:
        for key in form.errors:
            flash(f'{key} is required')

    return redirect(url_for('show_media',md5=form.data['media_id']))

@app.route('/comment/<cp_id>', methods=['POST'])
@limiter.exempt
def comment_file_by_cp_id(cp_id):
    form = CommentForm(meta={"csrf": False})
    if form.validate_on_submit():
        if form.data['media_id'] == 'supersecret':
            media = Media.query.filter_by(cp_id=cp_id).first()
            if media:
                comment = Comment(media_id=media.md5, content=form.data['content'],name=form.data['name'])
                save_changes(comment)
                media.comment_count += 1
                save_changes(media)
            return {'msg': 'success'}, 200
    else:
        for key in form.errors:
            flash(f'{key} is required')
    return {'msg': 'could not save comment', "error":form.errors}, 500


@app.route('/vote', methods=['POST'])
@limiter.limit("10 per minute")
def vote_file():
    form = VoteForm(meta={"csrf": False})
    if form.validate_on_submit():
        #if check_ip(request.remote_addr):

        media = Media.query.filter_by(md5=form.data['md5']).first_or_404()
        vote = Vote.query.filter_by(media_id=media.md5, ip=request.remote_addr).order_by(Vote.time.desc()).first()
        if not vote or datetime.utcnow() > (vote.time + timedelta(hours=24)):
            if form.data['vote'] == 'up':
                media.votes += 1
            elif form.data['vote'] == 'down':
                media.votes -= 1

            vote = Vote(ip=request.remote_addr, media_id=media.md5)
            if not current_user.is_anonymous:
                modify_credit_balance(current_user, 10, 'Received 10 Credits for voting')
            db.session.add(vote)
            db.session.add(media)
            db.session.commit()

            return {'msg': 'success'}, 200
    else:
        flash("You can't vote while using vpn")
    return {'msg': 'could not save vote'}, 400


@app.route('/report', methods=['POST'])
@limiter.limit("10 per minute")
def report_file():
    form = ReportForm()
    if form.validate_on_submit():
        if check_ip(request.remote_addr):

            media = Media.query.get(form.data['md5'])
            if len(media.reports.all()) >= 2:
                flash("The image has previously deemed appropriate for this site. Please contact dmca@chatpic.exposed with full contact information as required for a valid takedown request.")
                return {'msg': 'could not save report'}, 200
            if media:
                media.reported = True
                save_changes(media)
                report = Report(media_md5=form.data['md5'], reason=form.data['reason'], comment=form.data['comment'], email=form.data['email'],ip=request.remote_addr, status='new')
                if not current_user.is_anonymous:
                    report.reported_by = current_user.username
                    report.email = current_user.email
                save_changes(report)
            flash('The image has been reported')
            response = make_response({'msg': 'success'})
            return response, 200
        else:
            flash("You can't report while using vpn")
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')
    return {'msg': 'could not save report'}, 200

@app.route('/report/<cp_id>', methods=['POST'])
@limiter.exempt
def report_file_cp_id(cp_id):
    form = ReportForm(meta={"csrf": False})
    if form.validate_on_submit() and form.data['md5'] == "supersecret":
        media = Media.query.filter_by(cp_id=cp_id).first()
        if media:
            media.reported = True
            save_changes(media)
            report = Report(media_md5=media.md5, reason=form.data['reason'], comment=form.data['comment'], email="report@chatpic.exposed")
            save_changes(report)
            return {'msg': 'success'}, 200
    return {'msg': 'could not save report'}, 400

@app.route('/reports/')
@login_required
def reported_media():

    page = request.args.get('page', 1, type=int)
    if current_user.has_roles('admin'):
        media = Report.query.filter_by(status='new').order_by(
            Report.date.desc()).paginate(page, app.config['POSTS_PER_PAGE'], True)
        response = make_response(render_template('user_reports.html', media=media))
    else:
        media = Report.query.filter_by(reported_by=current_user.username).order_by(
            Report.date.desc()).paginate(page, app.config['POSTS_PER_PAGE'], True)
        response = make_response(render_template('user_reports.html', media=media))

    return response

@app.route('/reports/restore/<md5>')
@roles_required('admin')
def restore_media(md5):
    media = Media.query.get(md5)
    reports = Report.query.filter_by(media_md5=md5).all()

    if media and reports:
        media.reported = False
        for report in reports:
            report.status = 'restored'
            save_changes(report)
        save_changes(media)
        flash("Image restored")
    return redirect(url_for('reported_media'))

@app.route('/reports/restore/all')
@roles_required('admin')
def restore_all_media():
    media = Media.query.filter(Media.upload_time).filter_by(hidden=False, reported=True).all()
    for one in media:
        one.reported = False
        save_changes(one)
        for report in one.reports:
            report.status = 'restored'
            save_changes(report)
    flash(f"{len(media)} Images Restored")
    return redirect(url_for('reported_media'))

@app.route('/reports/remove/all')
@roles_required('admin')
def remove_all_media():
    media = Media.query.filter(Media.upload_time).filter_by(hidden=False, reported=True).all()
    for one in media:
        delete_media(one.filename,one.thumbnail)
        one.hidden = True
        db.session.add(one)
        reports = Report.query.filter_by(media_md5=one.md5).all()
        for report in reports:
            report.status = 'removed'
            db.session.add(report)
            if 'Underage' in report.reason or 'Dox (Reveal of personal information)' in report.reason:
                user = User.query.filter_by(username = reports[0].reported_by).first()
                if user:
                    modify_credit_balance(user, 100, 'Received 100 Credits for successfull reporting an illegal image')
    db.session.commit()

    flash(f"{len(media)} Images Removed")
    return redirect(url_for('reported_media'))

@app.route('/reports/remove/<md5>')
@login_required
def remove_media(md5):
    if current_user.has_roles('admin'):
        if md5.startswith('anon'):
            media = Media.query.filter_by(uploader=md5, hidden=False).all()
        else:
            media = Media.query.filter_by(md5=md5).all()
        for one in media:
            reports = Report.query.filter_by(media_md5=one.md5).all()
            for report in reports:
                report.status = 'removed'
                db.session.add(report)
                if 'Underage' in report.reason or 'Dox (Reveal of personal information)' in report.reason:
                    user = User.query.filter_by(username = reports[0].reported_by).first()
                    if user:
                        modify_credit_balance(user, 100,
                                              'Received 100 Credits for successfull reporting an illegal image')
            delete_media(one.filename,one.thumbnail)
            one.hidden = True
            db.session.add(one)
            db.session.commit()
            flash(f"{len(media)} Images Removed")
    else:
        if current_user.has_roles('free_delete'):
            media = Media.query.filter_by(md5=md5).first_or_404()
            media.hidden = True
            db.session.add(media)
        elif current_user.credits - 1000 >= 0:
            media = Media.query.filter_by(md5=md5).first_or_404()
            #delete_media(media.filename,media.thumbnail)
            media.hidden = True
            db.session.add(media)
            modify_credit_balance(current_user, -1000, f'Removed image {md5}')
            db.session.add(current_user)
        else:
            flash('Not enough credits to remove image')
        db.session.commit()
    return redirect(url_for('reported_media'))

@app.route('/faq')
def faq():
    markdown = """# Reports
If you believe that your work has been copied in a way that constitutes copyright infringement, please provide our copyright agent the written information specified below. Please note that this procedure is exclusively for notifying chatpic.exposed that your copyrighted material has been infringed.

An electronic or physical signature of the person authorized to act on behalf of the owner of the copyright interest;
A description of the copyrighted work that you claim has been infringed upon;
A description of where the material that you claim is infringing is located on the Site;
Your address, telephone number, and e-mail address;
A statement by you that you have a good-faith belief that the disputed use is not authorized by the copyright owner, its agent, or the law;
A statement by you, made under penalty of perjury, that the above information in your notice is accurate and that you are the copyright owner or authorized to act on the copyright owner’s behalf.
A link to the copyrighted material

*Mail your request exclusively to dmca@chatpic.exposed*"""
    return render_template('markdown.html', content=markdown), 200


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('429.html',e=e), 429



WEBHOOK_SECRET = '31a4dd5e-3744-4aff-817e-d857264b099f'

# using Flask
@app.route('/webhooks', methods=['POST'])
def webhooks():
    # event payload
    request_data = request.data.decode('utf-8')
    # webhook signature
    request_sig = request.headers.get('X-CC-Webhook-Signature', None)

    try:
        # signature verification and event object construction
        event = Webhook.construct_event(request_data, request_sig, WEBHOOK_SECRET)
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return str(e), 400

    print("Received event: id={id}, type={type}".format(id=event.id, type=event.type))
    print(event)
    order = Order.query.filter_by(id=event.data.id).first()

    if order:
        order.status = event.type
        order.updated_at = datetime.utcnow()
        save_changes(order)


    if event.type == 'charge:confirmed' or event.type == 'charge:resolved':
        user = User.query.filter_by(email=event.data.metadata.email).first()
        if event.data.name == '1.000 Credits':
            modify_credit_balance(user, 1000, 'Bought 1.000 Credits')
        elif event.data.name == '5.000 Credits':
            modify_credit_balance(user, 5000, 'Bought 5.000 Credits')
            assign_role_to_user('free_download', user)
        elif event.data.name == '10.000 Credits':
            modify_credit_balance(user, 10000, 'Bought 10.000 Credits')
            assign_role_to_user('free_download', user)
            assign_role_to_user('realtime_access', user)
        elif event.data.name == '50.000 Credits':
            modify_credit_balance(user, 50000, 'Bought 50.000 Credits')
            assign_role_to_user('free_download', user)
            assign_role_to_user('realtime_access', user)
        elif event.data.name == '100.000 Credits':
            modify_credit_balance(user, 100000, 'Bought 100.000 Credits')
            assign_role_to_user('free_download', user)
            assign_role_to_user('free_delete_user', user)
            assign_role_to_user('realtime_access', user)
    if not order and event.type == 'charge:created':
        order = Order(id=event.data.id, status=event.type,
                      created_at=datetime.strptime(event.data.created_at, '%Y-%m-%dT%H:%M:%SZ'), item=event.data.name,
                      )
        if event.data.name == 'chatpic.exposed':
            order.email = 'donations@chatpic.exposed'
            return 'success', 200
        else:
            order.email = event.data.metadata.email
        save_changes(order)
    #send_mail(order.email,order, event)
    return 'success', 200


def send_mail(recipient, order, event):
    return True
    if event.type == 'charge:created':
        msg = Message(f"Order for {order.item} has been created",
                      recipients=[recipient])
        msg.html = f'Thank you for purchasing {order.item}. <br> To see your order status click <a href="{event.data.hosted_url}">here</a> <br> To download your file click <a href="{url_for("get_download",id=order.id, _external=True)}">here</a><br>Please be aware: The download link is only valid 24h after the payment completed.'
        msg.body = f'Thank you for purchasing {order.item}. \n To see your order status go to {event.data.hosted_url}\n To download your file go to {url_for("get_download",id=order.id, _external=True)}\nPlease be aware: The download link is only valid 24h after the payment completed.'
    elif event.type == 'charge:failed':
        msg = Message(f"Order for {order.item} has not been paid",
                      recipients=[recipient])
        msg.html = f'Unfortunately your order for {order.item} was not successfull. <br> To see your order status click <a href="{event.data.hosted_url}">here</a>'
        msg.body = f'Unfortunately your order for {order.item} was not successfull. \n To see your order status go to {event.data.hosted_url}'
    elif event.type == 'charge:confirmed' or event.type == 'charge:delayed':
        msg = Message(f"Order for {order.item} completed",
                      recipients=[recipient])
        msg.html = f'Your order for {order.item} was fully paid. <br> To download your file click <a href="{url_for("get_download",id=order.id, _external=True)}">here</a><br>Please be aware: The download link is only valid 24h after the payment completed.'
        msg.body = f'Your order for {order.item} was fully paid. \n To download your file go to {url_for("get_download",id=order.id, _external=True)}\nPlease be aware: The download link is only valid 24h after the payment completed.'

    else:
        msg = Message(f"[DEBUG]Order created",
                      recipients=['admin@chatpic.exposed'])
        msg.html = f"Order has been created as {order.id} <br> {event}"

    msg.bcc = ["admin@chatpic.exposed"]
    msg.sender =("chatpic.exposed Order management", "notifications@chatpic.exposed")
    mail.send(msg)

@app.route('/media/<md5>/download')
@login_required
def get_download(md5):
    if current_user.has_roles('free_download'):
        media = Media.query.filter_by(md5=md5, hidden=False).first_or_404()
        return redirect(f"{app.config['CDN_URL']}{media.filename}")
    elif current_user.credits - 100 >= 0:
        modify_credit_balance(current_user, -100, 'Paid 100 Credits for downloading an image')
        media = Media.query.filter_by(md5=md5, hidden=False).first_or_404()
        return redirect(f"{app.config['CDN_URL']}{media.filename}")
    else:
        flash('You do not have enough credits to download this file. 100 Credits required')
        return redirect(url_for('show_media',md5=md5))
#def get_download(id):
#    order = Order.query.filter_by(id=id).first_or_404()
#    mapping = {
#        "Chatpic.exposed Pictures only": "chatpic.exposed-pictures.7z",
#        "Chatpic.exposed Videos only": "chatpic.exposed-videos.7z",
#        "Chatpic.exposed Full archive": "chatpic.exposed-full.7z",
#    }
#    if order.status == 'charge:confirmed' or order.status == 'charge:delayed':
#        if datetime.utcnow() > order.updated_at + timedelta(hours=24):
#            flash("Your download expired")
#        else:
#            url = f'/download/{mapping[order.item]}'
#            hash, expires = sign_url(url, 100, 'aitho5tinaih7Oogh8piokehae6tho1o')
#            flash(Markup(f"Your download can be found <a href='https://media.chatpic.exposed{url}?st={hash}&e={expires}'>here"))
#            return redirect(f'https://media.chatpic.exposed{url}?st={hash}&e={expires}')
#    else:
#        flash("Your payment has not yet completed. Please check your mails")
#
#    return redirect(url_for('index'))


@app.route('/profile/credits')
@login_required
def get_credit_history():
    page = request.args.get('page', 1, type=int)
    credit_transactions = CreditTransaction.query.filter_by(user_id=current_user.id).order_by(CreditTransaction.id.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], True)
    return render_template('credits_transaction.html', trans=credit_transactions)

@app.route('/profile/credits/buy')
@login_required
def buy_credits():
    return render_template('buy_credits.html')