from extensions import db

class LessonTrainer(db.Model):
    __tablename__ = 'lesson_trainers'
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)

    lesson = db.relationship('Lesson', back_populates='trainers')
    user = db.relationship('User')
