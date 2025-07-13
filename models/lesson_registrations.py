from extensions import db

class LessonRegistration(db.Model):
    __tablename__ = 'lesson_registrations'
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    registered_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (db.UniqueConstraint('lesson_id', 'user_id', name='_lesson_user_uc'),)

    lesson = db.relationship('Lesson', back_populates='registrations')
    user = db.relationship('User')
