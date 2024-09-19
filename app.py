from flask import Flask, render_template, request, redirect, url_for, session, flash, app
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.validators import DataRequired,Length
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:4b%233uXfCF%242@localhost/VPNCustdb'
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



class Data(db.Model):
    __tablename__="Custdata"
    id=db.Column(db.Integer,primary_key=True)
    first_name= db.Column(db.String(50))
    last_name= db.Column(db.String(50))
    email=db.Column(db.String(120),unique=True)
    password=db.Column(db.String(128),unique=True)#for hashing the password increase string length

    def __init__(self,first_name,last_name,email,password):
        self.first_name= first_name
        self.last_name= last_name
        self.email=email
        self.password=password

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    message = request.args.get('message')
    message_type = request.args.get('message_type')
    return render_template('index.html', message=message, message_type=message_type)

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# @app.route("/signup", methods=['POST','GET'])
# def signup():
#     form = Accntcreation()
#     if request.method == 'POST' and form.validate_on_submit():
@app.route("/signup", methods=['POST', 'GET'])
def signup():
    form = Accntcreation()
    login_form = Loginform()  # Create an instance of the login form
    if request.method == 'POST' and form.validate_on_submit():

        session.permanent= True
        # first_name = request.form['first_name']
        # last_name = request.form['last_name']
        # email = request.form['email']
        # password = request.form['password']
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


        data = Data(first_name, last_name, email, hashed_password)
        try:
            db.session.add(data)   
            db.session.commit()
            return redirect(url_for('index', message='Registration Successful', message_type='success'))
    
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
    



@app.route("/login", methods=['POST'])
def login():
    form = Loginform()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = Data.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['email'] = user.email
            session['user_name'] = user.first_name  # Store the user's first name
            return render_template("index.Html", form=form, message='Login Successful', message_type='success', )
            # return redirect(url_for('index'))  
        else:
            return redirect(url_for('index', message='Invalid email or password', message_type='failure'))
    return render_template("index.html", form=form)  # Render the login template
@app.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('user_name', None)
    return redirect(url_for('index', message='Logged out successfully', message_type='success'))
    

if __name__ == "__main__":
    app.debug=True
    app.run(debug=True)
