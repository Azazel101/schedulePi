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

from datetime            import datetime,date,timedelta,time

import threading

import OPi.GPIO          as GPIO
import smbus


def get_Host_name_IP(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        print("Hostname :  ",host_name) 
        print("IP : ",host_ip) 
    except: 
        print("Unable to get Hostname and IP")

def setup_gpio():
    print('Setting GPIO....')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    pins = Pin.query.all()
    for pin in pins:
        if pin.io: # Output
            print('Set OUTPUT : ', pin.pin)
            GPIO.setup(pin.pin, GPIO.OUT, initial=GPIO.HIGH)
        else: # Input
            print('Set INPUT : ', pin.pin)
            GPIO.setup(pin.pin, GPIO.IN)

def scan_i2c():
    bus = smbus.SMBus(0) # 1 indicates /dev/i2c-0

    for device in range(128):

        try:
            bus.read_byte(device)
            print(hex(device))
        except: # exception if read_byte fails
            pass


def schedule_task():
    past_minut = 0
    off_pin = {}
    # While loop
    print('Start schedule...')
    while True:
        now = datetime.now()
        if now.minute != past_minut:
            dailyschedule = DailySchedule.query.all()
            db.session.commit()
            #print('Schedule trigger :', now.hour, now.minute)
            for schedule in dailyschedule:
                if schedule.time.hour == now.hour and schedule.time.minute == now.minute:
                    print('Schedule SET :(',schedule.time.hour ,':', schedule.time.minute, ') - pin :', schedule.pin)
                    GPIO.output(schedule.pin, False)
                    off_pin[schedule.pin] = now + timedelta(minutes=schedule.duration)

            if off_pin:
                for key,value in off_pin.items():
                    if value.hour == now.hour and value.minute == now.minute:
                        print('Schedule RESET :(',value.hour, ':', value.minute, ') - pin : ' , key)
                        GPIO.output(key, True)

        past_minut = now.minute


# Setup
@app.before_first_request
def initialize():
    db.create_all()
    GPIO.cleanup()
    setup_gpio()
    global thread,ip_req
    ip_req = []
    thread = threading.Thread(target=schedule_task, name = 'Schedule')
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

    pin_status = {}
    used_pin = []
    for pin in pins: # read status of pin
        pin_status[pin.pin] = GPIO.input(pin.pin)
        used_pin.append(pin.pin)

    # tracking all ip to access
    if request.remote_addr not in ip_req:
        ip_req.append(request.remote_addr)

    days= ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    avalible_pins = [3,5,7,8,10,11,12,13,15,16,18,19,21,22,23,24,26]

    for pin in used_pin: # delete used pin
        avalible_pins.remove(pin)

    dayname = days[weekday]

    isalive = thread.isAlive()

    return render_template("index.html", 
                            dailyschedule=dailyschedule,
                            weeklyschedule=weeklyschedule,
                            hour=hour,
                            minute=minute,
                            weekday=weekday,
                            pins=pins,
                            pin_status=pin_status,
                            dayname=dayname,
                            avalible_pins=avalible_pins,
                            ip_req=ip_req,
                            isalive=isalive)


# ---------------------------------------- ADD

@app.route('/addpin', methods=['POST'])
def addpin():
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin']
        io = bool(int(request.form['io']))
        newpin = Pin(name=name, pin=pin, io=io)
        db.session.add(newpin)
        db.session.commit()

        if io: # Output
            print('Set OUTPUT : ', pin)
            GPIO.setup(int(pin), GPIO.OUT, initial=GPIO.HIGH)
        else: # Input
            print('Set INPUT : ', pin)
            GPIO.setup(int(pin), GPIO.IN)
        
        flash(f'Sucessfull add!', 'success')
        return redirect(url_for('index'))


@app.route('/adddaily', methods=['POST'])
def adddaily():
    if request.method == 'POST':
        time = request.form['time']
        name = request.form['name']
        duration = request.form['duration']
        time_object = datetime.strptime(time, '%H:%M').time()
        get_pin = Pin.query.filter_by(name=str(name)).first()
        newdail = DailySchedule(time=time_object, name=str(name), pin=int(get_pin.pin), duration=int(duration))
        db.session.add(newdail)
        db.session.commit()
        flash(f'Sucessfully add!', 'success')

        return redirect(url_for('index'))

# ---------------------------------------- EDIT

@app.route('/editdaily/<int:id>', methods=['POST'])
def editdaily(id):
    if request.method == 'POST':
        data = DailySchedule.query.filter_by(id=id).first()
        time = request.form['time']

        if len(time) >= 6:
            data.time = datetime.strptime(time, '%H:%M:%S').time()
        else:
            data.time = datetime.strptime(time, '%H:%M').time()
    
        data.name = request.form['name']
        data.duration = int(request.form['duration'])
        get_pin = Pin.query.filter_by(name=str(data.name)).first()
        data.pin = get_pin.pin
        db.session.commit()
        flash(f'Sucessfully update!', 'warning')
        return redirect(url_for('index'))

# ---------------------------------------- DELETE

@app.route('/delpin/<id>')
def delpin(id):
    delpin = Pin.query.filter_by(id=id).first()
    deldaily = DailySchedule.query.filter_by(name=str(delpin.name))
    if deldaily : 
        for delete in deldaily:
            db.session.delete(delete)
    db.session.delete(delpin)
    db.session.commit()
    flash(f'Sucessfully delete!', 'danger')

    return redirect(url_for('index'))

@app.route('/deldaily/<id>')
def deldaily(id):
    deldaily = DailySchedule.query.filter_by(id=id).first()
    db.session.delete(deldaily)
    db.session.commit()
    flash(f'Sucessfully delete!', 'danger')

    return redirect(url_for('index'))

# ---------------------------------------- GPIO - ON/OFF
@app.route("/on/<int:id>")
def gpio_on(id):
    GPIO.output(id, True)
    return redirect(url_for('index'))


@app.route("/off/<int:id>")
def gpio_off(id):
    GPIO.output(id, False)
    return redirect(url_for('index'))

@app.route("/all_off")
def all_off():
    pins = Pin.query.all()
    for pin in pins:
        if pin.io: GPIO.output(pin.pin, True)
    return redirect(url_for('index'))

@app.route("/all_on")
def all_on():
    pins = Pin.query.all()
    for pin in pins:
        if pin.io: GPIO.output(pin.pin, False)
    return redirect(url_for('index'))
# ---------------------------------------- TASK

@app.route("/task")
def task():
    global thread
    thread = threading.Thread(target=schedule_task, name = 'Schedule')
    thread.daemon = True
    thread.start()
    return redirect(url_for('index'))

@app.route("/func")
def func():
    scan_i2c()
    return redirect(url_for('index'))

@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200