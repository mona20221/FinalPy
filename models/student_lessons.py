from extensions import db


class StudentLesson(db.Model):
    __tablename__ = 'student_lesson'

    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True)
    termin_id = db.Column(db.Integer, db.ForeignKey('lesson_termin.id', ondelete='SET NULL'), nullable=True)
    registered_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship('Student', backref=db.backref('lessons', cascade='all, delete'))
    lesson = db.relationship('Lesson', backref=db.backref('students', cascade='all, delete'))
    termin = db.relationship('LessonTermin', backref=db.backref('student_lessons'))