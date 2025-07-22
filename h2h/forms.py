from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField,IntegerField, PasswordField, SubmitField, BooleanField,TextAreaField, SelectField
from wtforms.validators import DataRequired, Length,Email, EqualTo, ValidationError, NumberRange
from h2h.models import User
from phonenumbers import parse, format_number, PhoneNumberFormat, is_valid_number,phonenumberutil
from wtforms.fields import TelField
from flask_login import current_user


class RegistrationFrom(FlaskForm):
    number = StringField('Whatsapp Number',
                           validators=[DataRequired()])
    username = StringField('Username', 
                           validators=[DataRequired(), Length(2,20)])
    email = StringField('Email', validators=[DataRequired(), Email() ])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_number(self,number):
        try:
            num= parse(number.data,'ZW')
            if not is_valid_number(num):
                raise ValidationError('Invalid phone number')
        except phonenumberutil.NumberParseException:
            raise ValidationError('Invalid phone number format. Please include country code')

        user=User.query.filter_by(number=number.data).first()
        if user:
            raise ValidationError('That number already in use ! Please choose another one') 
        
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email already in use ! Please choose another one')


class UpdateAccountForm(FlaskForm):
    number = StringField('Whatsapp Number',
                           validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email() ])
    username = StringField('Username', 
                           validators=[DataRequired(), Length(2,20)])
    submit = SubmitField('Update')

    def validate_number(self,number):
        try:
            num= parse(number.data,'ZW')
            if not is_valid_number(num):
                raise ValidationError('Invalid phone number')
        except phonenumberutil.NumberParseException:
            raise ValidationError('Invalid phone number format. Please include country code')
        
        string_num = format_number(num,PhoneNumberFormat.E164)
        if string_num != current_user.number:
            user = User.query.filter_by(number=string_num).first()
            if user:
                raise ValidationError('That number already in use ! Please choose another one')
        
    def validate_username(self,username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username already in use ! Please choose another one')

    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email already in use ! Please choose another one')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email() ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class ListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired() , NumberRange(min=0, message="Price must be at least 0.")])
    category = SelectField('Category',validators=[DataRequired()], choices=[('Electronic','Electronic'),('Fashion','Fashion'),('Home & Garden','Home & Garden'),('Health & Beauty','Health & Beauty'),('Sports & Outdoors','Sports & Outdoors'),('Toys & Games','Toys & Games'),('Automotive','Automotive'),('Books & Media','Books & Media'),('Pets','Pets'),('Arts & Crafts','Arts & Crafts'),('Services','Services'),('Food & Beverage','Food & Beverage')])
    location = SelectField('Location',validators=[DataRequired()],choices=[('Harare','Harare'),('Gweru','Gweru'),('Bulawayo','Bulawayo'),('Mutare','Mutare'),('Masvingo','Masvingo'),('Chinhoyi','Chinhoyi'),('Kwekwe','Kwekwe'),('Chitungwiza','Chitungwiza'),('Kadoma','Kadoma'),('Kariba','Kariba'),('Chimanimani','Chimanimani'),('Chipinge','Chipinge'),('Bindura','Bindura'),('Gokwe','Gokwe')])
    description = TextAreaField('Description',validators=[DataRequired()])
    picture = FileField('Picture',validators=[ DataRequired(),FileAllowed(['jpg','png','jpeg'])])
    submit = SubmitField('Create')



class UpdateListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=0, message="Price must be at least 0.")])
    category = SelectField('Category',validators=[DataRequired()], choices=[('Electronic','Electronic'),('Fashion','Fashion'),('Home & Garden','Home & Garden'),('Health & Beauty','Health & Beauty'),('Sports & Outdoors','Sports & Outdoors'),('Toys & Games','Toys & Games'),('Automotive','Automotive'),('Books & Media','Books & Media'),('Pets','Pets'),('Arts & Crafts','Arts & Crafts'),('Services','Services'),('Food & Beverage','Food & Beverage')])
    location = SelectField('Location',validators=[DataRequired()],choices=[('Harare','Harare'),('Gweru','Gweru'),('Bulawayo','Bulawayo'),('Mutare','Mutare'),('Masvingo','Masvingo'),('Chinhoyi','Chinhoyi'),('Kwekwe','Kwekwe'),('Chitungwiza','Chitungwiza'),('Kadoma','Kadoma'),('Kariba','Kariba'),('Chimanimani','Chimanimani'),('Chipinge','Chipinge'),('Bindura','Bindura'),('Gokwe','Gokwe')])
    description = TextAreaField('Description',validators=[DataRequired()])
    picture = FileField('Picture',validators=[ FileAllowed(['jpg','png','jpeg'])])
    submit = SubmitField('Create')
