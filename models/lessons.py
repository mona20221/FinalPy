from extensions import db

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100))
    level = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='active')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    trainers = db.relationship('LessonTrainer', back_populates='lesson', cascade='all, delete-orphan')
    registrations = db.relationship('LessonRegistration', back_populates='lesson', cascade='all, delete-orphan')
    terminy = db.relationship('LessonTermin', back_populates='lesson', cascade='all, delete-orphan')
