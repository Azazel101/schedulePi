# -*- encoding: utf-8 -*-

# Python modules
import os, logging 
import socket    # Get Host name and IP
import time

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory, send_file, flash, jsonify

# App modules
from app                 import app, db#, bc
from app.models          import Pin, DailySchedule, WeeklySchedule

from datetime            import datetime,date

import threading
from app.tasks           import threaded_task


def get_Host_name_IP(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        print("Hostname :  ",host_name) 
        print("IP : ",host_ip) 
    except: 
        print("Unable to get Hostname and IP")


def schedule_task():
    now = datetime.now()#.time().strftime("%H:%M")
    hour = now.hour
    minute = now.minute

    dailyschedule = DailySchedule.query.all()
    for schedule in dailyschedule:
        if schedule.time.hour == hour and schedule.time.minute == minute:
            print(schedule.pin)

# Setup database
@app.before_first_request
def initialize_database():
    db.create_all()
    global thread
    thread = threading.Thread(target=threaded_task, name = 'Schedule' , args=(20,))
    thread.daemon = True
    thread.start()


@app.route('/')
def index():
#    get_Host_name_IP()
    now = datetime.now()#.time().strftime("%H:%M")
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()

    pins = Pin.query.all()
    dailyschedule = DailySchedule.query.all()
    weeklyschedule = WeeklySchedule.query.all()

    days= ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

    avalible_pins = [3,5,7,8,10,11,12,13,15,16,18,19,21,22,23,24,26]

    dayname = days[weekday]

    isalive = thread.isAlive()

    return render_template("index.html", 
                            dailyschedule=dailyschedule,
                            weeklyschedule=weeklyschedule,
                            hour=hour,
                            minute=minute,
                            weekday=weekday,
                            pins=pins,
                            dayname=dayname,
                            avalible_pins=avalible_pins,
                            isalive=isalive)


# ---------------------------------------- ADD

@app.route('/addpin', methods=['POST'])
def addpin():
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin']
        io = request.form['io']
        print(name, pin, io)
        newpin = Pin(name=name, pin=pin, io=bool(io))
        db.session.add(newpin)
        db.session.commit()
        flash(f'Sucessfull add!')

        return redirect(url_for('index'))


@app.route('/adddaily', methods=['POST'])
def adddaily():
    if request.method == 'POST':
        time = request.form['time']
        name = request.form['name']
        duration = request.form['duration']
        time_object = datetime.strptime(time, '%H:%M').time()

        print(time,name,duration)
        get_pin = Pin.query.filter_by(name=str(name)).first()
        newdail = DailySchedule(time=time_object, name=str(name), pin=int(get_pin.pin), duration=int(duration))
        db.session.add(newdail)
        db.session.commit()
        flash(f'Sucessfully add!')

        return redirect(url_for('index'))

# ---------------------------------------- EDIT

@app.route('/editdaily/<int:id>', methods=['POST'])
def editdaily(id):
    if request.method == 'POST':
        data = DailySchedule.query.filter_by(id=id).first()
        time = request.form['time']
        data.name = request.form['name']
        data.duration = request.form['duration']
        get_pin = Pin.query.filter_by(name=str(data.name)).first()
        data.pin = get_pin.pin
        data.time = datetime.strptime(time, '%H:%M').time()
        db.session.commit()
        flash(f'Sucessfully update!')
        return redirect(url_for('index'))

# ---------------------------------------- DELETE

@app.route('/delpin/<id>')
def delpin(id):
    delpin = Pin.query.filter_by(id=id).first()
    db.session.delete(delpin)
    db.session.commit()
    flash(f'Sucessfully delete!')

    return redirect(url_for('index'))

@app.route('/deldaily/<id>')
def deldaily(id):
    deldaily = DailySchedule.query.filter_by(id=id).first()
    db.session.delete(deldaily)
    db.session.commit()
    flash(f'Sucessfully delete!')

    return redirect(url_for('index'))

# ---------------------------------------- TASK

@app.route("/task", defaults={'duration': 20})
@app.route("/task/<int:duration>")
def task(duration):
    global thread
    thread = threading.Thread(target=threaded_task, name = 'Schedule' , args=(duration,))
    thread.daemon = True
    thread.start()
    return redirect(url_for('index'))


@app.route("/gettask")
def gettask():
    return jsonify({'thread_is_alive': str(thread.isAlive())})

@app.route("/stoptask")
def stoptask():
    schedule_task()
    return jsonify({'thread_is_alive': True})