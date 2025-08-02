from flask import render_template, url_for, request,flash,abort, redirect,session
from sqlalchemy import or_,case
from h2h import app, db,bcrypt,supabase,paynow
from h2h.models import User, Listing,Payment
from h2h.forms import ListingForm, RegistrationFrom, UpdateListingForm, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from phonenumbers import parse ,format_number,PhoneNumberFormat
from urllib.parse import quote
import secrets
import os 
import uuid
import time
from datetime import datetime, timezone
from PIL import Image,ImageOps
import io



@app.route("/")
def home():
    if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
    return render_template('landing_page.html', title='H2H')

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
        flash(f'Welcome!', 'info')
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
     now_utc = datetime.now(timezone.utc)
     listings = Listing.query.order_by(case((Listing.boosted_until > now_utc, 1), else_=0).desc(),Listing.created_at.desc())

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
    query = request.args.get('q', '').strip()
    
    listings = get_filtered_listings(category=category,location=location,q=query,page=page)

    if request.headers.get("HX-Request"):
        # Only return the listings fragment if this is an HTMX request
        return render_template(
            "partial_results.html",
            listings=listings,
        )

    return render_template('dashboard.html', listings=listings, 
                           category=category,location=location,
                           categories=categories, locations=locations,q=query)

def upload_picture(form_picture):
     rand_hex = secrets.token_hex(8)
     _, f_ext = os.path.splitext(form_picture.filename)
     picture_fn = rand_hex + f_ext

     img = Image.open(form_picture)
     img = ImageOps.exif_transpose(img)
     img = img.convert('RGB')
     img.thumbnail(size=(400,400))

     img_bytes = io.BytesIO()
     img.save(img_bytes,format='JPEG')
     img_bytes.seek(0)

     file_bytes = img_bytes.read()
     try:      
         res = supabase.storage.from_('listing-images').upload(picture_fn,file=file_bytes)
     except Exception as e:
          print(f'error uploading the file :{e}')
     return picture_fn

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
          filename = upload_picture(form.picture.data)
          listing = Listing(title=title,image_file=filename ,description=description,
                             price=price, category=category,location=location ,author=current_user)
          db.session.add(listing)
          db.session.commit()
          flash('Listing created.', 'success')
          return redirect(url_for('user_listings', username=current_user.username))
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

     listing_url = url_for('listing', listing_id=listing.id, _external=True)

     message = f"Hi! I'm interested in your listing on HandToHand:\n\n{listing.title} — ${listing.price}\n\nIs it still available?\n{listing_url}"

     link = create_whatsapp_deeplink(number=number,message=message)

     return render_template('listing.html', listing=listing, whatsapp_link=link)

@app.route('/listing/<int:listing_id>/update',methods=['GET','POST'])
@login_required
def update_listing(listing_id):
     listing = Listing.query.get_or_404(listing_id)
     if listing.author != current_user:
          abort(403)
     form = UpdateListingForm()
     if form.validate_on_submit():
            listing.title = form.title.data
            listing.description=form.description.data
            listing.price=form.price.data
            listing.category=request.form.get('category','')
            listing.location=request.form.get('location','')
            try:
                if form.picture.data:
                #delete old picture from database upload new one 
                    res = supabase.storage.from_('listing-images').remove([listing.image_file])
                #upload new file and update file name 
                    listing.image_file = upload_picture(form.picture.data)
            except Exception as e:
                print(f'error updating the file :{e}')
            db.session.commit()
            flash('Listing has been updated.', 'success')
            return redirect(url_for('user_listings', username=current_user.username))
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

    #delete image from supabase 
     try:
        res = supabase.storage.from_('listing-images').remove([listing.image_file])
        print(res)
     except Exception as e:
        print(f'error deleting the file :{e}')

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
@login_required
def user_listings(username):
    page = request.args.get('page', 1,type=int)
    user = User.query.filter_by(username=username).first_or_404()
    listings = Listing.query.filter_by(author=user)\
          .order_by(Listing.created_at.desc())\
          .paginate(page=page, per_page=10)
    

    return render_template('user_listings.html', listings=listings, user=user, total=listings.total)

@app.route('/boost/info/<int:listing_id>')
@login_required
def boost_info(listing_id):
     return render_template('boost_info.html', listing_id =listing_id)

@app.route('/boost/listing/<int:listing_id>'  ,methods=['GET'])
@login_required
def boost_listing(listing_id):
    reference = str(uuid.uuid4())[:8]
    listing = Listing.query.filter_by(id=listing_id).first()
    email = listing.author.email
    payment = paynow.create_payment(reference=reference,auth_email=email)
    transaction_name = f'boost-{listing_id}'
    payment.add(transaction_name, 1.00)
    response = paynow.send(payment)

    if response.success:
         pollUrl = response.poll_url
         payment_record = Payment(
              reference=reference,
              transaction_name=transaction_name,
              amount=1.00,
              poll_url=pollUrl,
              user_id=listing.author.id
              )
         db.session.add(payment_record)
         db.session.commit()

         session['reference'] = reference

         return redirect(response.redirect_url)
    else:
        flash('Failed to create payment. Please try again later.','warning')
        return redirect(url_for('listing_manager'))


@app.route('/payment/result',methods=['GET','POST'])
@login_required
def payment_result():
    reference = session.get('reference')
    if not reference:
        flash("Payment reference not found.", "warning")
        return redirect(url_for('listing_manager'))

    payment = Payment.query.filter_by(reference=reference).first()
    if not payment:
        flash("Payment not found.", "warning")
        return redirect(url_for('listing_manager'))
    
    if not payment.poll_url:
        flash("Poll URL is missing.", "warning")
        return redirect(url_for('listing_manager'))
    
    time.sleep(10)
    
    status = paynow.check_transaction_status(payment.poll_url)
    payment.status= status.status.lower()

    db.session.commit()

    session.pop('reference')

    flash(f'Payment status: {status.status}' ,'info')
    return redirect(url_for('listing_manager'))

@app.route('/payment/webhook', methods=['POST'])
def payment_webhook():
     data = request.form
     reference = data.get('reference')
     status = data.get('status')
     poll_url = data.get('pollurl')

     if not reference or not status:
        return "Missing data", 400
     
     payment = Payment.query.filter_by(reference=reference).first()
     if not payment:
        return "Payment not found", 404
     
     payment.status = status.lower()
     payment.poll_url = poll_url or payment.poll_url
     db.session.commit()

     if status.lower() == "paid" and payment.transaction_name.startswith("boost-"):
        try:
            listing_id = int(payment.transaction_name.split("-")[1])
            listing = Listing.query.get(listing_id)
            if listing:
                listing.boost()
                db.session.commit()
                print(f"✅ Listing {listing.id} boosted until {listing.boosted_until}")
        except Exception as e:
            print("⚠️ Boost failed:", e)
            return "Error boosting listing", 500

     return "OK", 200

@app.route('/privacy')
def privacy():
     return render_template('privacy.html', title='Privacy Policy - HandToHand')

@app.route('/terms')
def terms():
     return render_template('terms.html', title='Terms of Service - HandToHand')

@app.route('/safety')
def safety():
     return render_template('safety.html', title='Safety Guidelines - HandToHand')

@app.route("/about")
def about():
    logout_user()
    return render_template('landing_page.html', title='H2H')

@app.route("/delete_account/<int:user_id>")
@login_required
def delete_account(user_id):
    user = User.query.filter_by(id=user_id).first()
    listings = user.listings
    #delete image from supabase 
    try:
        if listings:
            for listing in listings:
                res = supabase.storage.from_('listing-images').remove([listing.image_file])
                print(res)
    except Exception as e:
        print(f'error deleting the file :{e}')

    logout_user()

    db.session.delete(user)
    db.session.commit()

    flash('Account deleted','success')
    return redirect(url_for('home'))