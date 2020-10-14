from app         import db

class Pin(db.Model):
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    pin        = db.Column(db.Integer, nullable=False, unique=True)
    io         = db.Column(db.Boolean, nullable=False)
    name       = db.Column(db.String(30))
#    schedules  = db.relationship('schedule', backref='pin', lazy='dynamic')

    def __repr__(self):
        return self.name

class DailySchedule(db.Model):
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    time       = db.Column(db.Time)
    pin        = db.Column(db.Integer, nullable=False)#, db.ForeignKey('pin.pin')
    name       = db.Column(db.String(30))
    duration   = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.id

class WeeklySchedule(db.Model):
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    time       = db.Column(db.Time, nullable=False)
    pin        = db.Column(db.Integer, nullable=False)#, db.ForeignKey('pin.pin')
    name       = db.Column(db.String(30))
    duration   = db.Column(db.Integer, nullable=False)
    d1         = db.Column(db.Boolean)
    d2         = db.Column(db.Boolean)
    d3         = db.Column(db.Boolean)
    d4         = db.Column(db.Boolean)
    d5         = db.Column(db.Boolean)
    d6         = db.Column(db.Boolean)
    d7         = db.Column(db.Boolean)

    def __repr__(self):
        return self.id