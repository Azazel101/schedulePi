# -*- encoding: utf-8 -*-

# Python modules
import os, logging 
import socket    # Get Host name and IP
import time
import logging

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory, send_file, flash, jsonify

# App modules
from app                 import app, db#, bc
from app.models          import Pin, DailySchedule, WeeklySchedule

from datetime            import datetime,date,timedelta,time

import threading

import OPi.GPIO          as GPIO
import smbus

bus = smbus.SMBus(0) # 1 indicates /dev/i2c-0


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

def scan_i2c():
    bus = smbus.SMBus(0) # 1 indicates /dev/i2c-0
    print('i2c scan...')
    for device in range(128):

        try:
            bus.read_byte(device)
            print(hex(device))
        except: # exception if read_byte fails
            pass


def schedule_task():
    global off_pin

    past_minut = 0
    off_pin = {}
    # While loop
    print('Start schedule...')
    while True:
        now = datetime.now()
        weekday = now.weekday()

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
@app.before_first_request
def initialize():
    db.create_all()
    setup_gpio()
    global thread,ip_req
    ip_req = []
    thread = threading.Thread(target=schedule_task, name = 'Schedule')
    thread.daemon = True
    thread.start()

def TSL2561():
    # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
    # ch0 LSB, ch0 MSB
    data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
    # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
    # ch1 LSB, ch1 MSB
    data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)
    # Convert the data
    ch0 = data[1] * 256 + data[0]
    ch1 = data1[1] * 256 + data1[0]
    return [ch0, ch1]

def BMP280():
    # Get I2C bus
    # BMP280 address, 0x76(118)
    # Read data back from 0x88(136), 24 bytes
    b1 = bus.read_i2c_block_data(0x76, 0x88, 24)
    # Convert the data
    # Temp coefficents
    dig_T1 = b1[1] * 256 + b1[0]
    dig_T2 = b1[3] * 256 + b1[2]
    if dig_T2 > 32767 :
        dig_T2 -= 65536
    dig_T3 = b1[5] * 256 + b1[4]
    if dig_T3 > 32767 :
        dig_T3 -= 65536
    # Pressure coefficents
    dig_P1 = b1[7] * 256 + b1[6]
    dig_P2 = b1[9] * 256 + b1[8]
    if dig_P2 > 32767 :
        dig_P2 -= 65536
    dig_P3 = b1[11] * 256 + b1[10]
    if dig_P3 > 32767 :
        dig_P3 -= 65536
    dig_P4 = b1[13] * 256 + b1[12]
    if dig_P4 > 32767 :
        dig_P4 -= 65536
    dig_P5 = b1[15] * 256 + b1[14]
    if dig_P5 > 32767 :
        dig_P5 -= 65536
    dig_P6 = b1[17] * 256 + b1[16]
    if dig_P6 > 32767 :
        dig_P6 -= 65536
    dig_P7 = b1[19] * 256 + b1[18]
    if dig_P7 > 32767 :
        dig_P7 -= 65536
    dig_P8 = b1[21] * 256 + b1[20]
    if dig_P8 > 32767 :
        dig_P8 -= 65536
    dig_P9 = b1[23] * 256 + b1[22]
    if dig_P9 > 32767 :
        dig_P9 -= 65536

    # Read data back from 0xF7(247), 8 bytes
    # Pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB
    # Temperature xLSB, Humidity MSB, Humidity LSB
    data = bus.read_i2c_block_data(0x76, 0xF7, 8)
    # Convert pressure and temperature data to 19-bits
    adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
    adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16
    # Temperature offset calculations
    var1 = ((adc_t) / 16384.0 - (dig_T1) / 1024.0) * (dig_T2)
    var2 = (((adc_t) / 131072.0 - (dig_T1) / 8192.0) * ((adc_t)/131072.0 - (dig_T1)/8192.0)) * (dig_T3)
    t_fine = (var1 + var2)
    cTemp = (var1 + var2) / 5120.0
    fTemp = cTemp * 1.8 + 32
    # Pressure offset calculations
    var1 = (t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * (dig_P6) / 32768.0
    var2 = var2 + var1 * (dig_P5) * 2.0
    var2 = (var2 / 4.0) + ((dig_P4) * 65536.0)
    var1 = ((dig_P3) * var1 * var1 / 524288.0 + ( dig_P2) * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * (dig_P1)
    p = 1048576.0 - adc_p
    p = (p - (var2 / 4096.0)) * 6250.0 / var1
    var1 = (dig_P9) * p * p / 2147483648.0
    var2 = p * (dig_P8) / 32768.0
    pressure = (p + (var1 + var2 + (dig_P7)) / 16.0) / 100
    return [cTemp, fTemp, pressure]


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

@app.route('/delweekly/<id>')
def delweekly(id):
    delweekly = WeeklySchedule.query.filter_by(id=id).first()
    db.session.delete(delweekly)
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
    bus = smbus.SMBus(0) # 1 indicates /dev/i2c-0
    print(BMP280())
    return redirect(url_for('index'))

@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200