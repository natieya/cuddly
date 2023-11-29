# app.py

from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, PostForm
import os
import secrets
from db import init_app, db

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///site.db')
init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User, Post

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        # User is logged in, render dashboard or user-specific content
        posts = Post.query.filter_by(author=current_user).all()
        return render_template('dashboard.html', posts=posts)
    else:
        # User is not logged in, render public content
        posts = Post.query.all()
        return render_template('home.html', posts=posts)
        
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha512')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()

    if form.validate_on_submit():
        new_post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(new_post)
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', form=form)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if the current user is the author of the post
    if current_user != post.author:
        flash('You are not allowed to edit this post.', 'danger')
        return redirect(url_for('home'))

    form = PostForm()

    if form.validate_on_submit():
        # Update post logic here
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()

        flash('Your post has been updated!', 'success')
        return redirect(url_for('home'))

    # Pre-fill the form with the current post data
    form.title.data = post.title
    form.content.data = post.content

    return render_template('edit_post.html', form=form, post=post)


@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if the current user is the author of the post
    if current_user != post.author:
        flash('You are not allowed to delete this post.', 'danger')
        return redirect(url_for('home'))

    # Delete post logic here
    db.session.delete(post)
    db.session.commit()

    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
