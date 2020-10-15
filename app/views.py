# -*- encoding: utf-8 -*-

# Python modules
import os, logging 
import socket    # Get Host name and IP
import time
import logging
import requests

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory, send_file, flash, jsonify

# App modules
from app                 import app, db#, bc
from app.models          import Pin, DailySchedule, WeeklySchedule,API

from datetime            import datetime,date,timedelta,time

import threading

import OPi.GPIO          as GPIO
import smbus

bus = smbus.SMBus(0) # 1 indicates /dev/i2c-0

def checkInternetSocket(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False

def get_Host_name_IP(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        print("Hostname :   ",host_name) 
        print("IP : ",host_ip) 
    except: 
        print("Unable to get Hostname and IP")

def setup_gpio():
    print('Setting GPIO....')
    GPIO.cleanup()
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

def schedule_task():
    global off_pin,stop_threads, api_key, weather, sunrise, sunset

    stop_threads = False 
    past_minut = 0
    past_hour = 0
    off_pin = {}
    api_key = {}
    # While loop
    print('Start Thread...')
    while True:
        now = datetime.now()
        weekday = now.weekday()
        if stop_threads:
            print('Stop Thread...')
            stop_threads = False 
            break

        if now.hour != past_hour:
            print('Hour schedule...')
            apis = API.query.all()
            for api in apis:
                api_key[api.name] = api.api_key

            if checkInternetSocket():
                data = get_openweathermap_data('galanta')
                weather = data['weather'][0]['main']
                sunrise = datetime.fromtimestamp(int(data['sys']['sunrise']))
                sunset = datetime.fromtimestamp(int(data['sys']['sunset']))

        past_hour = now.hour


        if now.minute != past_minut:
            dailyschedule = DailySchedule.query.all()
            weeklyschedule = WeeklySchedule.query.all()
            db.session.commit()

            #DailySchedule
            for schedule in dailyschedule:
                if schedule.time.hour == now.hour and schedule.time.minute == now.minute:
                    print('DailySchedule SET :(',schedule.time.hour ,':', schedule.time.minute, ') - pin :', schedule.pin)
                    GPIO.output(schedule.pin, False)
                    off_pin[schedule.pin] = now + timedelta(minutes=schedule.duration)

            #WeekSchedule
            for schedule in weeklyschedule:
                actualday = [schedule.d1,schedule.d2,schedule.d3,schedule.d4,schedule.d5,schedule.d6,schedule.d7] 
                if actualday[weekday] and schedule.time.hour == now.hour and schedule.time.minute == now.minute:
                    print('WeekSchedule SET :(',schedule.time.hour ,':', schedule.time.minute, ') - pin :', schedule.pin)
                    GPIO.output(schedule.pin, False)
                    off_pin[schedule.pin] = now + timedelta(minutes=schedule.duration)

            #If active schedule then add to off
            if off_pin:
                for key,value in off_pin.items():
                    if value.hour == now.hour and value.minute == now.minute:
                        print('Schedule RESET :(',value.hour, ':', value.minute, ') - pin : ' , key)
                        GPIO.output(key, True)

        past_minut = now.minute

# Setup
#@app.before_first_request
def initialize():
    db.create_all()
    setup_gpio()
    global thread, ip_req, api_key
    ip_req = []

    thread = threading.Thread(target=schedule_task, name = 'Schedule')
    thread.daemon = True
    thread.start()

def get_openweathermap_data(city): # api_key['darksky']
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={ city }&units=metric&appid=' + api_key['openweathermap']
        r = requests.get(url, timeout=5).json()
        return r
    except requests.exceptions.Timeout as e: 
        print(e)

@app.route('/')
def index():
#    get_Host_name_IP()
    now = datetime.now()#.time().strftime("%H:%M")
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()

    pins = Pin.query.order_by(Pin.pin.asc()).all()
    dailyschedule = DailySchedule.query.all()
    weeklyschedule = WeeklySchedule.query.all()
    apis = API.query.all()

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
                            weather=weather,
                            sunrise=sunrise,
                            sunset=sunset,
                            apis=apis,
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
        GPIO.cleanup()
        setup_gpio()      
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

@app.route('/adddweekly', methods=['POST'])
def addweekly():
    if request.method == 'POST':
        time = request.form['time']
        name = request.form['name']
        duration = request.form['duration']
        day1 = request.form.get('day1')
        day2 = request.form.get('day2')
        day3 = request.form.get('day3')
        day4 = request.form.get('day4')
        day5 = request.form.get('day5')
        day6 = request.form.get('day6')
        day7 = request.form.get('day7')
        time_object = datetime.strptime(time, '%H:%M').time()
        get_pin = Pin.query.filter_by(name=str(name)).first()
        newweekly = WeeklySchedule(time=time_object, 
                                    name=str(name), 
                                    pin=int(get_pin.pin),
                                    duration=int(duration),
                                    d1=bool(day1),
                                    d2=bool(day2),
                                    d3=bool(day3),
                                    d4=bool(day4),
                                    d5=bool(day5),
                                    d6=bool(day6),
                                    d7=bool(day7))
        db.session.add(newweekly)
        db.session.commit()
        flash(f'Sucessfully add!', 'success')

        return redirect(url_for('index'))

@app.route('/addapi', methods=['POST'])
def addapi():
    if request.method == 'POST':
        name = request.form['name']
        api_key = request.form['api_key']
        newapi = API(name=name, api_key=api_key)
        db.session.add(newapi)
        db.session.commit()
        flash(f'Sucessfull add!', 'success')
        return redirect(url_for('index'))

# ---------------------------------------- EDIT
@app.route('/editpin/<int:id>', methods=['POST'])
def editpin(id):
    if request.method == 'POST':
        data = Pin.query.filter_by(id=id).first()
        data.name = request.form['name']
        db.session.commit()
        flash(f'Sucessfully update!', 'warning')
        return redirect(url_for('index'))

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

@app.route('/editweekly/<int:id>', methods=['POST'])
def editweekly(id):
    if request.method == 'POST':
        data = WeeklySchedule.query.filter_by(id=id).first()
        time = request.form['time']

        if len(time) >= 6:
            data.time = datetime.strptime(time, '%H:%M:%S').time()
        else:
            data.time = datetime.strptime(time, '%H:%M').time()
    
        data.name = request.form['name']
        data.duration = int(request.form['duration'])
        data.d1 = bool(request.form.get('day1'))
        data.d2 = bool(request.form.get('day2'))
        data.d3 = bool(request.form.get('day3'))
        data.d4 = bool(request.form.get('day4'))
        data.d5 = bool(request.form.get('day5'))
        data.d6 = bool(request.form.get('day6'))
        data.d7 = bool(request.form.get('day7'))
        get_pin = Pin.query.filter_by(name=str(data.name)).first()
        data.pin = get_pin.pin
        db.session.commit()
        flash(f'Sucessfully update!', 'warning')
        return redirect(url_for('index'))

@app.route('/editapi/<int:id>', methods=['POST'])
def editapi(id):
    if request.method == 'POST':
        data = API.query.filter_by(id=id).first()
        data.name = request.form['name']
        data.api_key = request.form['api_key']
        db.session.commit()
        flash(f'Sucessfully update!', 'warning')
        return redirect(url_for('index'))

# ---------------------------------------- DELETE

@app.route('/delpin/<id>')
def delpin(id):
    delpin = Pin.query.filter_by(id=id).first()
    deldaily = DailySchedule.query.filter_by(name=str(delpin.name))
    delweekly = DailySchedule.query.filter_by(name=str(delpin.name))
    if deldaily : 
        for delete in deldaily:
            db.session.delete(delete)
    if delweekly : 
        for delete in delweekly:
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

@app.route('/delweekly/<id>')
def delweekly(id):
    delweekly = WeeklySchedule.query.filter_by(id=id).first()
    db.session.delete(delweekly)
    db.session.commit()
    flash(f'Sucessfully delete!', 'danger')

    return redirect(url_for('index'))

@app.route('/delapi/<id>')
def delapi(id):
    delapi = API.query.filter_by(id=id).first()
    db.session.delete(delapi)
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

# ---------------------------------------- Activate Schedule
@app.route('/activeweekly/<int:id>')
def activeweekly(id):
    now = datetime.now()
    active = WeeklySchedule.query.filter_by(id=id).first()
    db.session.commit()
    GPIO.output(active.pin, False)
    off_pin[active.pin] = now + timedelta(minutes=active.duration)
    flash(f'Sucessfully active!', 'primary')
    return redirect(url_for('index'))

@app.route('/activedaily/<int:id>')
def activedaily(id):
    now = datetime.now()
    active = DailySchedule.query.filter_by(id=id).first()
    db.session.commit()
    GPIO.output(active.pin, False)
    off_pin[active.pin] = now + timedelta(minutes=active.duration)
    flash(f'Sucessfully active!', 'primary')
    return redirect(url_for('index'))

# ---------------------------------------- Thread

@app.route("/thread/list")
def thread_list():
    thread_list = []
    for thread in threading.enumerate(): 
        thread_list.append(thread.name)
    return jsonify(thread_list)

@app.route("/thread/run")
def thread_run():
    global thread
    thread = threading.Thread(target=schedule_task, name = 'Schedule')
    thread.daemon = True
    thread.start()
    return redirect(url_for('index'))

@app.route("/thread/stop")
def thread_stop():
    global stop_threads
    stop_threads = True 
    return redirect(url_for('index'))

# ---------------------------------------- Check NET

@app.route("/checknet")
def checknet():
    data = checkInternetSocket()
    return jsonify(data)

# ---------------------------------------- Weather

@app.route("/weather/<city>")
def weather(city):
    data = get_openweathermap_data(city)
    weather = data['weather'][0]['main']
    sunrise = datetime.fromtimestamp(int(data['sys']['sunrise']))
    sunset = datetime.fromtimestamp(int(data['sys']['sunset']))
    print(sunrise,sunset)
    if 'rain' in data:
        print(data['rain'])
    return jsonify(data)

# ---------------------------------------- Get IP
@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return jsonify({
                    'your_ip': request.remote_addr,
                    'all_accessed_ip': ip_req
                    }), 200
