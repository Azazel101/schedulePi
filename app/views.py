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
from app.forms           import PinForm, DailyScheduleForm

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
        if schedule.date.hour == hour and schedule.date.minute == minute:
            print(schedule.pin)



@app.route('/')
def index():
    pinform = PinForm()
    dailyform = DailyScheduleForm()
#    get_Host_name_IP()
    now = datetime.now()#.time().strftime("%H:%M")
    hour = now.hour
    minute = now.minute
    weekday = now.weekday() + 1

    pins = Pin.query.all()
    dailyschedule = DailySchedule.query.all()
    weeklyschedule = WeeklySchedule.query.all()

    return render_template("index.html", 
                            pinform=pinform,
                            dailyschedule=dailyschedule,
                            weeklyschedule=weeklyschedule,
                            dailyform = dailyform,
                            hour=hour,
                            minute=minute,
                            weekday=weekday,
                            pins=pins)


# ---------------------------------------- ADD

@app.route('/addpin', methods=['POST'])
def addpin():
    form = PinForm()
#    if form.validate_on_submit():
    name = form.Name.data
    pin = form.Pin.data
    kluc = dict(form.IO.choices)
    for key, value in kluc.items(): 
        if form.IO.data == value: 
            io = key
    print(pin,name)
    print(form.IO.data)
    newpin = Pin(name=name, pin=pin, io=io)
    db.session.add(newpin)
    db.session.commit()
#    flash(f'Sucessfull add!')

    return redirect(url_for('index'))
#    return redirect(url_for('index'))


@app.route('/adddaily', methods=['POST'])
def adddaily():
    form = DailyScheduleForm()
    time = form.Time.data
    name = form.Pin.data
    duration = form.Duration.data
    get_pin = Pin.query.filter_by(name=str(name)).first()
    newdail = DailySchedule(date=time, pin=get_pin.pin, duration=duration)
    db.session.add(newdail)
    db.session.commit()
#    flash(f'Sucessfull add!')

    return redirect(url_for('index'))
# ---------------------------------------- DELETE

@app.route('/delpin/<id>')
def delpin(id):
    delpin = Pin.query.filter_by(id=id).first()
    db.session.delete(delpin)
    db.session.commit()
#    flash(f'Sucessfull add!')

    return redirect(url_for('index'))

@app.route('/deldaily/<id>')
def deldaily(id):
    deldaily = DailySchedule.query.filter_by(id=id).first()
    db.session.delete(deldaily)
    db.session.commit()
#    flash(f'Sucessfull add!')

    return redirect(url_for('index'))

# ---------------------------------------- TASK

@app.route("/task", defaults={'duration': 5})
@app.route("/task/<int:duration>")
def task(duration):
    global thread
    thread = threading.Thread(target=threaded_task, name = 'schedule' , args=(duration,))
    thread.daemon = True
    thread.start()
    return jsonify({'thread_name': str(thread.name),
                    'started': True})

@app.route("/gettask")
def gettask():
    return jsonify({'thread_is_alive': str(thread.isAlive())})

@app.route("/stoptask")
def stoptask():
    schedule_task()
    return jsonify({'thread_is_alive': True})