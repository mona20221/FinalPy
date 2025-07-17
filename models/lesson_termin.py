from extensions import db

class LessonTermin(db.Model):
    __tablename__ = 'lesson_termin'

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False)
    datum = db.Column(db.Date, nullable=False)
    cas = db.Column(db.Time, nullable=False)
    miesto = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    lesson = db.relationship('Lesson', back_populates='terminy')
