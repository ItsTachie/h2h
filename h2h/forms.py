from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField,IntegerField, PasswordField, SubmitField, BooleanField,TextAreaField, SelectField
from wtforms.validators import DataRequired, Length,Email, EqualTo, ValidationError
from h2h.models import User
import phonenumbers
from wtforms.fields import TelField
from flask_login import current_user


class RegistrationFrom(FlaskForm):
    number = TelField('Whatsapp Number',
                           validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email() ])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_number(self,number):
        try:
            parsed_number = phonenumbers.parse(number.data, 'ZW')
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError('Invalid phone number.')
            
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError('Invalid phone number format')
        
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email already in use ! Please choose another one')

'''
class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(2,20)])
    email = StringField('Email', validators=[DataRequired(), Email() ])
    picture = FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png','jpeg'])])
    submit = SubmitField('Update')

    def validate_username(self,username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken ! Please choose another one')

    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email already in use ! Please choose another one')
'''

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email() ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class ListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    category = SelectField('Category',validators=[DataRequired()], choices=[('electronics','Electronic'),('fashion','Fashion'),('home&garden','Home & Garden'),('health&beauty','health&beauty'),('sports&outdoors','Sports & Outdoors'),('toys&games','Toys & Games'),('automotive','Automotive'),('books&media','Books & Media'),('pets','Pets'),('arts&crafts','Arts & Crafts'),('services','Services'),('food&beverage','Food & Beverage')])
    location = SelectField('Location',validators=[DataRequired()],choices=[('gweru','Gweru'),('harare','Harare'),('bulawayo','Bulawayo'),('mutare','Mutare'),('masvingo','Masvingo'),('chinhoyi','Chinhoyi'),('kwekwe','Kwekwe'),('chitungwiza','Chitungwiza'),('kadoma','Kadoma'),('kariba','Kariba'),('chimanimani','Chimanimani'),('chipinge','Chipinge'),('bindura','Bindura'),('Gokwe','Gokwe')])
    description = TextAreaField('Description',validators=[DataRequired()])
    submit = SubmitField('Create')