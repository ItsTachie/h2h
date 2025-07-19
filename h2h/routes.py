from flask import render_template, url_for, request,flash,abort, redirect
from h2h import app, db,bcrypt
from h2h.models import User, Listing
from h2h.forms import ListingForm, RegistrationFrom, LoginForm
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
def home():
    form = ListingForm()
    return render_template('landing_page.html', title='Hand2Hand', form=form)

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if current_user.is_authenticated:
            return redirect(url_for('home'))
    form = RegistrationFrom()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(number=form.number.data, email=form.email.data, password=hashed_password )
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to login', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Signup',form=form)

@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
            return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))