from flask import render_template, url_for, request,flash,abort, redirect
from sqlalchemy import or_
from h2h import app, db,bcrypt
from h2h.models import User, Listing
from h2h.forms import ListingForm, RegistrationFrom, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from phonenumbers import parse ,format_number,PhoneNumberFormat
from urllib.parse import quote

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
        login_user(user, remember=True)
        flash(f'Welcome', 'info')
        return redirect(url_for('dashboard'))
    return render_template('signup.html', title='Signup',form=form)

@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password !', 'error')
    return render_template('login.html', title='Login',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def get_filtered_listings(category=None,location=None,q=None,page=1,per_page=10):
     listings = Listing.query.order_by(Listing.created_at.desc())
 
     if category and category!= 'None':
         listings = listings.filter_by(category=category)
     if location and location != 'None':
         listings = listings.filter_by(location=location)
     if q:
         listings = listings.filter(or_(Listing.title.ilike(f"%{q}%"),Listing.description.ilike(f"%{q}%")
            )
        )

     paginated_listings = listings.paginate(page=page, per_page=per_page)

     return paginated_listings

@app.route('/dashboard')
@login_required
def dashboard():
    form = ListingForm()
    categories = [ choice[1] for choice in form.category.choices]
    locations = [ choice[1] for choice in form.location.choices]

    page = request.args.get('page', 1,type=int)

    category = request.args.get('category')
    location = request.args.get('location')
    query = request.args.get('q', '')
    
    listings=get_filtered_listings(category=category,location=location,q=query,page=page)

    if request.headers.get("HX-Request"):
        # Only return the listings fragment if this is an HTMX request
        return render_template(
            "partial_results.html",
            listings=listings
        )
    
    total=listings.total

    return render_template('dashboard.html', listings=listings, 
                           category=category,location=location,
                           categories=categories, locations=locations,q=query, total=total)



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
          return redirect(url_for('listing_manager'))
     return render_template('new_listing.html', title='New Listing', legend='New Listing',form=form)

def create_whatsapp_deeplink(number,message):
     cleaned_num = number.replace('+', '').replace(' ','')
     encoded_message = quote(message)
     return f'https://wa.me/{cleaned_num}?text={encoded_message}'

@app.route('/listing/<int:listing_id>')
@login_required
def listing(listing_id):
     listing = Listing.query.get_or_404(listing_id)
     seller = listing.author
     number = seller.number

     message = f"Hi, I'm interested in your listing on H2H. \n {listing.title} - {listing.price} \n link url"
     link = create_whatsapp_deeplink(number=number,message=message)

     return render_template('listing.html', listing=listing, whatsapp_link=link)

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
        
     return render_template('new_listing.html', title='Edit Listing', legend='Edit Listing',form=form)

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
    if request.method == 'GET':
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

@app.route('/user/<string:username>')
def user_listings(username):
    page = request.args.get('page', 1,type=int)
    user = User.query.filter_by(username=username).first_or_404()
    listings = Listing.query.filter_by(author=user)\
          .order_by(Listing.created_at.desc())\
          .paginate(page=page, per_page=9)
    
          
    return render_template('user_listings.html', listings=listings, user=user, total=listings.total)
'''
@app.route('/boost/listing/<int:listing_id>'  ,methods=['GET'])
def boost_listing(listing_id):
    
    return render_template('boost.html')'''