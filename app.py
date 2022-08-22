import os
import json
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import matplotlib.pyplot as plt
from sympy import PythonIntegerRing


cur_path = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///maddy.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    
app.config['SECRET_KEY'] = "key"
db = SQLAlchemy(session_options={"autoflush": False})
db.init_app(app)
app.app_context().push()

def to_date(string):
    d_t = (string.split('-'))

#models
class Cli(db.Model):
    _tablename_ = 'cli'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String, nullable = False, unique = True)
    email = db.Column(db.String, nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

class Tp(db.Model):
    _tablename_ = 'tp'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    cli_id = db.Column(db.Integer, db.ForeignKey('cli.id'), nullable = False)
    name = db.Column(db.String, nullable = False, unique = True)
    input_type = db.Column(db.String)
    settings = db.Column(db.String)
    priority = db.Column(db.String, nullable = False)
    def __init__(self, cli_id, name, input_type, settings='None', priority='high'):
        self.cli_id = cli_id
        self.name = name
        self.input_type = input_type
        self.settings = settings
        self.priority = priority

class Dat(db.Model):
    _tablename_ = 'dat'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    tp_id = db.Column(db.Integer, db.ForeignKey('tp.id'), nullable = False)
    date = db.Column(db.String, nullable = False)
    value = db.Column(db.String, nullable = False)
    details = db.Column(db.String)
    def __init__(self, tp_id, date, value, details):
        self.tp_id = tp_id
        self.value = value
        self.details = details
        self.date = date
#login check
def is_logged_in():
    if 'logged_in' in session:
        return True
    else:
        return False


#home page
@app.route("/")
@app.route('/home')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    tp = Tp.query.filter_by(cli_id = session['id']).all()
    return render_template('home.html', session = session, tp = tp)
    
#login page
@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        form = request.form
        cli = Cli.query.filter_by(username = form.get('username'), email = form.get('email'), password = form.get('password')).all()
        if cli != []:
            session['logged_in'] = True
            session['id'] = cli[0].id
            session['username'] = form.get('username')
            session['email'] = form.get('email')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password')

    return render_template('login.html', session = session)

#registration page
@app.route("/register", methods = ['POST', 'GET'])
def register():
    if request.method == 'POST':
        form = request.form
        if form.get('password') == form.get('password2'):
            new_cli = Cli(form['username'], form['email'], form['password'])
            db.session.add(new_cli)
            db.session.commit()
        else:
            flash("Password confirmation denied")
            return redirect(url_for('register'))
    return render_template('register.html', session = session)

#add tracker
@app.route("/tp/add", methods=['GET', 'POST'])
def add_tp():
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        form = request.form
        if form.get('settings') != "":
            new_tp = Tp(session['id'], form.get('name'), form.get('options'), form.get('priority'), str(form.get('settings').split(',')))
        else:
            new_tp = Tp(session['id'], form.get('name'), form.get('options'), form.get('priority'))
        db.session.add(new_tp)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_trackers.html')

#edit tracker
@app.route("/tp/<tp_id>/edit", methods = ['GET', 'POST'])
def edit_tp(tp_id):
    tp = Tp.query.filter_by(id = tp_id).first()
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        form  =request.form
        cur_tp = Tp.query.filter_by(id = tp_id).first()
        cur_tp.name = form.get('name')
        cur_tp.input_type = form.get('type')
        cur_tp.settings = form.get('settings')
        logs_in_tp = Dat.query.filter_by(tp_id=tp_id).all()
        for log in logs_in_tp:
            db.session.delete(log)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_trackers.html', tp=tp)

#delete tracker
@app.route("/tp/<tp_id>/delete")
def remove_tp(tp_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    to_be_removed = Tp.query.filter_by(id = tp_id).first()
    db.session.delete(to_be_removed)
    log_in_tp = Dat.query.filter_by(tp_id=tp_id).all()
    for log in log_in_tp:
        db.session.delete(log_in_tp)
    db.session.commit()
    return redirect(url_for('home'))

#add log in tracker
@app.route("/tp/<tp_id>/records/add", methods = ['POST', 'GET'])
def add_record(tp_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    tp = Tp.query.filter_by(id = tp_id).first()
    options = None
    if tp.input_type == "Multiple Choice":
        options = tp.settings.split(',')
    if request.method == 'POST':
        form = request.form
        value = None
        if tp.input_type == "Numerical":
            value = int(form.get('value'))
            new_log = Dat(tp_id, datetime.today().strftime('%Y-%m-%d'),value, form.get('details'))
        if tp.input_type == "Multiple Choice":
            value = form.get('value')
            new_log = Dat(tp_id, datetime.today().strftime('%Y-%m-%d'),value, form.get('details'))
        if tp.input_type == "Timestamp":
            value = form.get('value')
            new_log = Dat(tp_id, datetime.today().strftime('%Y-%m-%d at %H-%M-%S'), value, form.get('details'))

        db.session.add(new_log)
        db.session.commit()
        return redirect(f'/tp/{tp_id}/view')


    return render_template('add_record.html', tp = tp, options = options)

#view log
@app.route("/tp/<tp_id>/view")
def view_tp(tp_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    tp = Tp.query.filter_by(id = tp_id).first()
    dat = Dat.query.filter_by(tp_id = str(tp_id)).all()
    mor = Dat.query.filter_by(tp_id = str(tp_id),details='morning').all()
    eve = Dat.query.filter_by(tp_id = str(tp_id),details='evenning').all()
    aft = Dat.query.filter_by(tp_id = str(tp_id),details='afternoon').all()
    sume=0
    ll=[]
    for d in mor :
        sume=int(sume)+int(d.value)
    print(sume)
   
    ll.append(sume)
    sume=0
    for d in eve :
            sume=int(sume)+int(d.value)
    print(sume)
   
    ll.append(sume)
    sume=0
    for d in aft :
            sume=int(sume)+int(d.value)
    print(sume)
   
    ll.append(sume)

      
    
    if dat!=[]:
        if tp.input_type == "Numerical":
            min_date = date(int(dat[0].date.split('-')[0]), int(dat[0].date.split('-')[1]), int(dat[0].date.split('-')[2]))
            Y = [(date(int(dat.date.split('-')[0]), int(dat.date.split('-')[1]), int(dat.date.split('-')[2]))-min_date) .days for dat in dat]
            X = [int(dat.value) for dat in dat]
           
        elif tp.input_type == "Multiple Choice":
            dat_data = {}
            options = tp.settings.split(',')
            for dat in dat:
                value = None
                for i in range(len(options)):
                    if options[i] == dat.value:
                        value = i
                        break
                if options[value] not in dat_data:
                    dat_data[dat.value] = 1
                else:
                    dat_data[dat.value] = dat_data[dat.value]+1
            values = dat_data.values()
  


           

    return render_template('view_trackers.html', tp_id = tp_id, dat = dat, tp=tp,ll=json.dumps(ll))

#edit log
@app.route("/tp/<tp_id>/dat/<dat_id>", methods = ['GET', 'POST'])
def edit_logs(tp_id, dat_id):
    tp = Tp.query.filter_by(id = tp_id).first()
    dat = Dat.query.filter_by(id = dat_id).first()
    options = tp.settings.split(',')
    if request.method == "POST":
        form = request.form
        if form.get('submit') == "Delete":
            db.session.delete(dat)
            db.session.commit()
            return redirect(f'/tp/{tp_id}/view')
        if form.get('submit') == "Edit":
            if tp.input_type == "Numerical":
                dat.tp_id = tp_id
                dat.date = form.get('date')
                dat.value = form.get('value')
                dat.details = form.get('details')
            elif tp.input_type == "Multiple Choice":
                dat.tp_id = tp_id
                dat.value = form.get('value')
                dat.details = form.get('details')
            else:
                dat.tp_id = tp_id
                dat.value = form.get('value')
                dat.details = form.get('details')
            db.session.commit()
            return redirect(f'/tp/{tp_id}/view')

    return render_template('edit_logs.html', tp = tp, dat = dat ,options = options,)
#logout
@app.route("/logout")
def logout():
    session.pop('logged_in')
    return redirect(url_for('login'))


#run
if __name__ == "__main__":
    app.run(debug=True)