from extensions import db

class Member(db.Model):
    __tablename__ = 'members'
    member_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    registration_date = db.Column(db.DateTime, server_default=db.func.now())


    users = db.relationship('User', back_populates='member',  cascade='all, delete-orphan')


    @property
    def full_name(self):
            return f"{self.first_name} {self.last_name}"