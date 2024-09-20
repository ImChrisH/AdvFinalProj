from flask import Flask, render_template, request, redirect, url_for, session, flash, app, Response
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.validators import DataRequired,Length
from flask_wtf.csrf import CSRFProtect
from datetime import datetime




app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:9658@localhost/VPNCustomerdb'
db = SQLAlchemy(app)
app.permanent_session_lifetime= timedelta(days=1)



#create a user accnt creation form class
class Accntcreation(FlaskForm):
    first_name=StringField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your first name"})
    last_name=StringField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your last name"})
    email=StringField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your email id"})
    password=PasswordField("",validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long")],
        render_kw={"placeholder": "Enter your password"})
    submit_create= SubmitField("Create Account")

    #create a login form class
class Loginform(FlaskForm):
    email=StringField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your email id"})
    password=PasswordField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your password"})
    submit_login= SubmitField("Login")

class Updtepasswrd(FlaskForm):
    password_old=PasswordField("",validators=[DataRequired()],render_kw={"placeholder": "Enter your old password"})
    password_new=PasswordField("",validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long")],
        render_kw={"placeholder": "Enter your new password"})
    confirm_password_new=PasswordField("",validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long")],
        render_kw={"placeholder": "Re-enter your password"})
    submit= SubmitField("submit")


# Customer data db model

class Data(db.Model):
    __tablename__="Custdata"
    id=db.Column(db.Integer,primary_key=True)
    first_name= db.Column(db.String(50))
    last_name= db.Column(db.String(50))
    email=db.Column(db.String(120),unique=True)
    password=db.Column(db.String(128),unique=True)#for hashing the password increase string length
    image_id= db.Column(db.Integer, db.ForeignKey('images.id')) 

    image =db.relationship('Img', backref='user_image', lazy=True)

    def __init__(self,first_name,last_name,email,password):
        self.first_name= first_name
        self.last_name= last_name
        self.email=email
        self.password=password

# Password Audit model

class password_audit2(db.Model):
    __tablename__ = 'password_audit2'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Custdata.id', ondelete='CASCADE'))
    old_password = db.Column(db.String(128), nullable=False)
    change_date_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, user_id, old_password):
        self.user_id = user_id
        self.old_password = old_password
        self.change_date_time = datetime.now()

# IMAGE Model

class Img(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.LargeBinary, nullable=False)  # For storing the image data
    mimetype = db.Column(db.String(120), nullable=False)  # For storing the image type
    name = db.Column(db.String(120), nullable=False)  # For storing the filename

    def __init__(self, img, mimetype, name):
        self.img = img
        self.mimetype = mimetype
        self.name = name

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    message = request.args.get('message')
    message_type = request.args.get('message_type')
    user = Data.query.filter_by(email=session.get('email')).first()
    return render_template('index.html', user=user,message=message, message_type=message_type)


# PRICING ROUTE

@app.route("/pricing")
def pricing():
    user = Data.query.filter_by(email=session.get('email')).first()
    return render_template("pricing.html",user=user)

# CONTACT ROUTE

@app.route("/contact")
def contact():
    user = Data.query.filter_by(email=session.get('email')).first()
    return render_template("contact.html",user=user)

# @app.route("/signup", methods=['POST','GET'])
# def signup():
#     form = Accntcreation()
#     if request.method == 'POST' and form.validate_on_submit():



# SIGNUP ROUTE

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    form = Accntcreation()
    login_form = Loginform()  # Create an instance of the login form
    if request.method == 'POST' and form.validate_on_submit():

        session.permanent= True
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        # Generate a hashed version of the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        print(first_name)
        # Output the hashed password
        print(hashed_password)
        print(f"First Name: {first_name}, Last Name: {last_name}, Email: {email}, Hashed Password: {hashed_password}")
        user = Data.query.filter_by(email=session.get('email')).first()

        data = Data(first_name, last_name, email, hashed_password)
        try:
            db.session.add(data)   
            db.session.commit()
            return redirect(url_for('index',user=user, message='Registration Successful', message_type='success'))
    
        except IntegrityError as e:
            db.session.rollback()
            if 'unique constraint' in str(e):
                flash('Email or phone number already exists.', 'danger')
                return redirect(url_for('index', message='Account already exists', message_type='exists'))
            else:
                flash(f'An error occurred: {e}', 'danger')
                return redirect(url_for('signup', f'An error occurred: {e}', message_type='failure'))
    else:
        print(form.errors)
    # return render_template("signup.html", form= form)
    return render_template("signup.html", form=form, login_form=login_form)  # Pass both forms
    

# LOGIN ROUTE:

@app.route("/login", methods=['POST'])
def login():
    form = Loginform()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = Data.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['email'] = user.email
            session['user_name'] = user.first_name.title() # Store the user's first name
            return render_template("index.Html", form=form, message='Login Successful', message_type='success',user=user )
            # return redirect(url_for('index')) 
        else:
            return redirect(url_for('index', message='Invalid email or password', message_type='failure'))
    return render_template("index.html", form=form,user=user)  # Render the login template

# UPDATE ROUTE

@app.route("/updte_psswrd", methods=['GET', 'POST'])
def updte_psswrd():
    update_form = Updtepasswrd()
    if request.method == 'POST' and update_form.validate_on_submit():
        if 'email' not in session:
            return redirect(url_for('index', message='login to your account first'))  # Redirect to login if the user is not logged in

        
        # Get the user's information from the session
        user = Data.query.filter_by(email=session['email']).first()
        
        # Check if the old password entered by the user matches the current password
        if user and check_password_hash(user.password, update_form.password_old.data):

            old_password_entry = password_audit2(user_id=user.id, old_password=user.password)
            db.session.add(old_password_entry)
            
            # Ensure the new password and confirmation match
            if update_form.password_new.data == update_form.confirm_password_new.data:
                # Hash the new password
                hashed_password = generate_password_hash(update_form.password_new.data, method='pbkdf2:sha256')

                # Update the password in the database
                user.password = hashed_password
                db.session.commit()

                flash('Password updated successfully', 'success')
                return redirect(url_for('index', message='Password updated successfully', message_type='success'))
            else:
                flash('Old password is incorrect', 'danger')
                return redirect(url_for('updte_psswrd', message='Old password is incorrect', message_type='failure'))
    
    return render_template('updte_psswrd.html', update_form= update_form)    

# PROFILE ROUTE

@app.route("/profile")
def profile():
    if 'email' not in session:
        return redirect(url_for('index', message='You need to log in first', message_type='warning'))
    
    user = Data.query.filter_by(email=session['email']).first()
    current_time = datetime.now()  # No formatting here
    
    form = Updtepasswrd()

    return render_template("profile.html", user=user, current_time=current_time, form=form)



#UPLOAD IMAGE ROUTE

@app.route('/upload', methods=['POST'])
def upload():
    pic = request.files['pic']

    if not pic:
        return 'No picture uploaded', 400
    
    #Saving the image
    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype
    img = Img(img=pic.read(), mimetype=mimetype, name=filename)

    #Adding to db
    db.session.add(img)
    db.session.commit()

     # Pairing image with user
    user = Data.query.filter_by(email=session['email']).first()
    user.image = img  # Associate the uploaded image
    db.session.commit()

    return redirect(url_for('profile', message='Image has been uploaded', message_type='success'))


# IMAGE ROUTE
@app.route('/image/<int:image_id>')
def get_image(image_id):
    # Creating Image Object
    img = Img.query.get(image_id)

    if img:
        return Response(img.img, mimetype=img.mimetype)
    return 'Image not found', 404

# LOGOUT ROUTE

@app.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('user_name', None)
    return redirect(url_for('index', message='Logged out successfully', message_type='success'))
    

if __name__ == "__main__":
    app.debug=True
    app.run(debug=True)
