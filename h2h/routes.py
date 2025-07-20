from flask import render_template, url_for, request,flash,abort, redirect
from h2h import app, db,bcrypt
from h2h.models import User, Listing
from h2h.forms import ListingForm, RegistrationFrom, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from phonenumbers import parse ,format_number,PhoneNumberFormat


@app.route("/")
def home():
    if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
    return render_template('landing_page.html', title='Hand2Hand')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
    form = RegistrationFrom()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        num_obj = parse(form.number.data,'ZW')
        number= format_number(num_obj,PhoneNumberFormat.E164)
        user = User(username=form.username.data, number=number, email=form.email.data, password=hashed_password )
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
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            print('no user found')
            flash('Login unsuccessful. Please check email and password !', 'error')
    return render_template('login.html', title='Login',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    listings = Listing.query.all()
    return render_template('dashboard.html', listings=listings)

@app.route('/listing/new', methods=['GET','POST'])
@login_required
def new_listing():
     form = ListingForm()
     if form.validate_on_submit():
          title = form.title.data
          description=form.description.data
          price=form.price.data
          category=request.form.get('category','')
          location=request.form.get('location','')
          listing = Listing(title=title, description=description,
                             price=price, category=category,location=location ,author=current_user)
          db.session.add(listing)
          db.session.commit()
          flash('Listing created.', 'success')
          return redirect(url_for('dashboard'))
     return render_template('new_listing.html', title='New Listing', legend='New Listing',form=form)

@app.route('/listing/<int:listing_id>')
@login_required
def listing(listing_id):
     listing = Listing.query.get_or_404(listing_id)
     return render_template('listing.html', listing=listing)

@app.route('/listing/<int:listing_id>/update',methods=['GET','POST'])
@login_required
def update_listing(listing_id):
     listing = Listing.query.get_or_404(listing_id)
     if listing.author != current_user:
          abort(403)
     form = ListingForm()
     if form.validate_on_submit():
            listing.title = form.title.data
            listing.description=form.description.data
            listing.price=form.price.data
            listing.category=request.form.get('category','')
            listing.location=request.form.get('location','')
            db.session.commit()
            flash('Listing has been updated.', 'success')
            return redirect(url_for('listing_manager'))
     elif request.method =='GET':
          form.submit.label.text ='Update'
          form.title.data = listing.title
          form.description.data= listing.description
          form.price.data= listing.price
          form.category.data= listing.category
          form.location.data = listing.location
        
     return render_template('new_listing.html', title='Update Listing', legend='Update Listing',form=form)

@app.route('/listing/<int:listing_id>/delete',methods=['POST'])
@login_required
def delete_listing(listing_id):
     listing = Listing.query.get_or_404(listing_id)
     if listing.author != current_user:
          abort(403)
     db.session.delete(listing)
     db.session.commit()
     flash('Listing has been deleted.', 'success')
     return redirect(url_for('listing_manager'))

@app.route('/account', methods = ['GET','POST'])
@login_required
def account():   
    form = UpdateAccountForm()
    if form.validate_on_submit():
         current_user.username = form.username.data
         current_user.email = form.email.data
         num_obj = parse(form.number.data,'ZW')
         number= format_number(num_obj,PhoneNumberFormat.E164)
         current_user.number = number
         db.session.commit()
         flash('Account has been updated.', 'success')
         return redirect(url_for('account'))
    elif request.method == 'GET':
        #prefill the fields with the following information
        form.email.data = current_user.email
        form.number.data= current_user.number
        form.username.data=current_user.username
    return render_template('account.html', title='Account', form=form)



@app.route('/listings')
@login_required
def listing_manager():
     listings = Listing.query.filter_by(uid=current_user.id).all()
     return render_template('listing_manager.html', listings=listings, num_listings=len(listings))