from flask import Flask
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from extensions import db, bcrypt
from models import User, Member, Lesson, LessonRegistration, LessonTrainer, Message, Student, StudentLesson, LessonTermin
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mona123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://upu4ozux3dkb0kkpwusa:pWHFUECWXXcfGEo0poKdFWaiEI0cvv@b7zabufywrnnt4i8piy9-postgresql.services.clever-cloud.com:50013/b7zabufywrnnt4i8piy9'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # meno funkcie pre login route


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_now():
    return {'now': datetime.today()}

# Domovská stránka
@app.route('/')
def index():
    lessons = Lesson.query.filter_by(status='active').order_by(Lesson.created_at.desc()).all()
    return render_template('index.html', lessons=lessons)


@app.route('/lessons/<int:lesson_id>')
def view_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id,status='active').first_or_404()

    trainers=[lt.user for lt in LessonTrainer.query.filter_by(lesson_id=lesson.id).all()]

    students_links = StudentLesson.query.filter_by(lesson_id=lesson.id).all()

    # vsetky terminy naraz
    termin_ids = [sl.termin_id for sl in students_links if sl.termin_id]

    # vsetky terminy ulozim do slovnika
    termins = {t.id: t for t in LessonTermin.query.filter(LessonTermin.id.in_(termin_ids)).all()}

    students_with_termin = []
    for sl in students_links:
        termin = termins.get(sl.termin_id)
        students_with_termin.append({
            'student': sl.student,
            'termin_datum': termin.datum if termin else None
        })

    terminy = lesson.terminy

    return render_template('lesson_detail.html', lesson=lesson, trainers=trainers, students_with_termin=students_with_termin, terminy=terminy)

@app.route('/lessons/<int:lesson_id>/join', methods=['POST'])
@login_required
def join_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, status='active').first_or_404()

    # ak student neexistuje, vytvor ho - ma rovnake id ako user
    student = Student.query.get(current_user.id)
    if not student:
        student = Student(student_id=current_user.id)
        db.session.add(student)
        db.session.commit()

    # overenie ci je student prihlaseny
    already_joined = StudentLesson.query.filter_by(
        lesson_id = lesson.id,
        student_id = current_user.id
    ).first()

    if already_joined:
        flash('Už ste prihlásený na tento kurz.', 'info')
    else:
        new_entry = StudentLesson(student_id=current_user.id, lesson_id=lesson.id)
        db.session.add(new_entry)
        db.session.commit()
        flash('Úspešne ste sa prihlásili na kurz.', 'success')

    return redirect(url_for('view_lesson', lesson_id=lesson.id))



@app.route('/lessons/create', methods=['GET', 'POST'])
def create_lesson():
    # if request.method == 'POST':

    # Tu bude logika na vytvorenie novej lekcie
    return "Tu bude formulár na vytvorenie lekcie"



# Registrácia
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash('Používateľ už existuje.', 'danger')
            return redirect(url_for('register'))
        if Member.query.filter_by(email=email).first():
            flash('Email je už registrovaný.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        # Vytvor člena
        member = Member(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        db.session.add(member)
        db.session.flush()  # načítaj member.id
        print("ID nového člena:", member.member_id)
        # Vytvor používateľa naviazaného na člena
        user = User(
            username=username,
            password_hash=hashed_pw,
            member_id=member.member_id
        )
        db.session.add(user)

        try:
            db.session.commit()
            flash('Registrácia úspešná, prihláste sa.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba pri registrácii: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')


# Prihlásenie
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Používateľ neexistuje. Chcete sa zaregistrovať?', 'confirm')
            return redirect(url_for('login', confirm_shown='true'))

        if user and user.check_password(password):
            login_user(user)
            flash('Prihlásenie úspešné.', 'success')
            return redirect(url_for('index'))

        flash('Neplatné prihlasovacie údaje.', 'danger')

    return render_template('login.html')

# Reset password
@app.route('/reset-password', methods= ['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        flash('Ak váš účet existuje, poslali sme na váš email inštrukcie k resetu hesla.', 'info')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

# Odhlásenie
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Odhlásili ste sa.')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
