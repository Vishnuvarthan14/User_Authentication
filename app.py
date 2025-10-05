from flask import Flask,render_template,request,jsonify,redirect,url_for,session
from flask_sqlalchemy import SQLAlchemy
from function import authenticate
from flask_mail import Mail,Message
from datetime import datetime,timedelta
from dotenv import load_dotenv
import os
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == 'True'
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)


class userDetails(db.Model):
    user_id = db.Column(db.Integer,primary_key = True)
    user_name=db.Column(db.String(50),nullable=False)
    user_mail = db.Column(db.String(100),nullable=False ,unique=True)
    user_password = db.Column(db.String(50),nullable=False)

    def __rep__(self):
        return f"user_id= {self.user_id} user_name ={self.name} user_mail={self.user_mail} user_password={self.user_password}"
    

with app.app_context():
    db.create_all()


@app.route('/',methods = ['POST','GET'])
def load():
    if request.method == 'POST':
        name = request.form['user_name']
        email = request.form['user_mail']
        password = request.form['user_password']
        exists = userDetails.query.filter_by(user_mail=email).first()
        if exists:
            data="User Already Exists"
            return render_template('index.html',data=data)
        user_detail = userDetails (
            user_name = name,
            user_mail=email,
            user_password = password
        )
        db.session.add(user_detail)
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/get',methods = ['GET'])
def get():
    datas = userDetails.query.all()
    processed =[]
    for data in datas:
        processed.append({
            'user_id': data.user_id,
            'user_name': data.user_name,
            'user_mail': data.user_mail,
            'user_password': data.user_password
        })
    return jsonify(processed)

@app.route('/get/<string:mail>',methods=['GET'])
def get_user(mail):
    data = userDetails.query.filter_by(user_mail=mail).first()
    if not data:
        return jsonify({'message':' User Not found'})
    
    processed = {'id':data.user_id,'name':data.user_name,'mail':data.user_mail,'password':data.user_password}
    return jsonify(processed)


@app.route('/login',methods=['POST','GET'])
def loginPage():
    if request.method =='POST':
        email = request.form['user_mail']
        password = request.form['user_password']

        if not email:
            return render_template('login.html',data='Enter your Email')
        if not password:
            return render_template('login.html')

        check = userDetails.query.filter_by(user_mail=email).first()
        if not check:
            return render_template('login.html',data='Invalid email or password')
        
        message = authenticate(email,password)
        if message['message']=='Success':
            return redirect(url_for('home'))
        else:
            return render_template('login.html',data=message['message'])

       
@app.route('/forget',methods = ['POST','GET'])
def forget():
    if request.method == 'POST':
        email = request.form['user_mail']
        if not email:
            return render_template('forget.html', data="Enter your email")
        otp = str(random.randint(100000,999999))
        session['otp'] = otp
        session['email'] = email
        session['otp_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = Message('Your OTP Verification Code',
                      sender=app.config['MAIL_USERNAME'],recipients=[email])
        msg.body = f"Your Verification Code is {otp}"
        try:
            mail.send(msg)
        except Exception as e:
            return render_template('forget.html',data='Unable to send Mail')

        return redirect(url_for('validate'))
    return render_template('forget.html')

@app.route('/validate',methods=['GET','POST'])
def validate():
    if request.method == 'POST':
        otp = request.form.get('user_OTP')

        otp_time = datetime.strptime(session.get('otp_time'),"%Y-%m-%d %H:%M:%S")
        if datetime.now()-otp_time> timedelta(minutes=1):
            session.pop('otp',None)
            session.pop('otp_time',None)
            return render_template('forget.html',data="Your OTP EXPIRED")

        if otp == session.get('otp'):
            session.pop('otp', None)
            return redirect(url_for('change'))
        return render_template('forget.html',data ='Invalid OTP')
    return render_template('forget.html')

@app.route('/change', methods=['GET','POST'])
def change():
    mail = session.get('email')
    if not mail:
        return redirect(url_for('forget'))

    if request.method == 'POST':
        new_pass = request.form['new_pass']
        user = userDetails.query.filter_by(user_mail=mail).first()
        if not user:
            return render_template('change_password.html', data='No Such User!')
        
        user.user_password = new_pass
        db.session.commit()
        session.pop('email', None)
        return redirect(url_for('login'))

    return render_template('change_password.html')


if __name__== '__main__':
    app.run(host="0.0.0.0", port=5000)
