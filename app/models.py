from app         import db

def check_length(attribute, length):
    """Checks the attribute's length."""
    try:
        return bool(attribute) and len(attribute) <= length
    except:
        return False

class Pin(db.Model):
    __tablename__ = "pin"
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    pin        = db.Column(db.Integer, nullable=False, unique=True)
    io         = db.Column(db.Boolean, nullable=False)
    name       = db.Column(db.String(128))
#    schedules  = db.relationship('schedule', backref='pin', lazy='dynamic')

    def __init__(self, name=None):
        self.name = name or "untitled"

    def __repr__(self):
        return f"<Pin: {self.name}>"

    @property
    def title(self):
        return self._title

#    @title.setter
#    def name(self, name):
#        if not check_length(name, 128):
#            raise ValueError(f"{name} is not a valid title")
#        self._name = name

class DailySchedule(db.Model):
#    __tablename__ = "dailyschedule"
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    time       = db.Column(db.Time)
    pin        = db.Column(db.Integer, nullable=False)#, db.ForeignKey('pin.pin')
    name       = db.Column(db.String(30))
    duration   = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.id

class WeeklySchedule(db.Model):
#    __tablename__ = "weeklyschedule"
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

class API(db.Model):
    id         = db.Column(db.Integer, primary_key=True, nullable=False)
    name       = db.Column(db.String(30), unique=True)
    api_key    = db.Column(db.String(255), unique=True)
#    city       = db.Column(db.String(30))
#    temp       = db.Column(db.Float, nullable=True)
#    precip     = db.Column(db.Float, nullable=True)