import os

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from form import RegisterForm, LoginForm, AddPostForm,MessageForm
from model import db, User, Follow, Post, PostLike,Message

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devsecret")
app.config["WTF_CSRF_ENABLED"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///social_media.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    if current_user.is_authenticated:
        users = User.query.filter(User.id != current_user.id).all()
        follows = Follow.query.filter_by(follower_id=current_user.id).all()
        followed_ids = [f.followed_id for f in follows]
    else:
        users = User.query.all()
        followed_ids = []
    return render_template("index.html", users=users, follows=followed_ids)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. You can log in.", 'success')
        return redirect(url_for("login"))

    return render_template('/register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("index"))

        flash("Invalid username or password")

    return render_template("login.html", form=form)


@app.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    exist = Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user_id
    ).first()
    if not exist:
        db.session.add(Follow(
            follower_id=current_user.id,
            followed_id=user_id
        ))
        db.session.commit()
    return redirect(request.referrer)


@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user_id
    ).delete()
    db.session.commit()
    return redirect(request.referrer)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    is_my_profile = (user_id == current_user.id)
    posts = Post.query.filter_by(author_id=user_id)
    is_following = False
    if not is_my_profile:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first() is not None

    liked_post_ids = {
        like.post_id
        for like in PostLike.query.filter_by(users_id=current_user.id).all()
    }

    post_like_counts = {
        post.id: PostLike.query.filter_by(post_id=post.id).count()
        for post in posts
    }
    return render_template(
        "profile.html", user=user, is_own_profile=is_my_profile, is_following=is_following, posts=posts,
        liked_post_ids=liked_post_ids,
        post_like_counts=post_like_counts, )


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)

    if other_user.id == current_user.id:
        flash("You can't chat with yourself")
        return redirect(url_for("index"))

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content_hash = '67',
            content=form.content.data
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("chat", user_id=user_id))

    messages = Message.query.filter(
        db.or_(
            db.and_(
                Message.sender_id == current_user.id,
                Message.receiver_id == other_user.id
            ),
            db.and_(
                Message.sender_id == other_user.id,
                Message.receiver_id == current_user.id
            )
        )
    ).order_by(Message.created_at.asc()).all()

    return render_template(
        "chat.html",
        other_user=other_user,
        messages=messages,
        form=form
    )


@app.route('/add_post', methods=['POST', 'GET'])
def add_post():
    form = AddPostForm()

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            author_id=current_user.id,
            text=form.text.data
        )
        db.session.add(post)
        db.session.commit()
        flash('Post was created successfully!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))

    return render_template("add_post.html", form=form)


@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)

    like = PostLike.query.filter_by(
        users_id=current_user.id,
        post_id=post.id
    ).first()

    if like:
        db.session.delete(like)
    else:
        new_like = PostLike(
            users_id=current_user.id,
            post_id=post.id
        )
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
