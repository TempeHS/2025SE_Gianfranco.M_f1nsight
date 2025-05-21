from .. import db

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    grand_prix = db.Column(db.String(64), nullable=False)
    driver = db.Column(db.String(64), nullable=False)
    position = db.Column(db.Integer)
    time = db.Column(db.String(32))

    def __repr__(self):
        return f'<RaceResult {self.year} - {self.grand_prix} - {self.driver}>'
