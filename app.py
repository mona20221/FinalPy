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
@login_required
def create_lesson():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        subject = request.form.get('subject')
        level = request.form.get('level')
        termin_datum = request.form.get('termin_datum')
        termin_cas = request.form.get('termin_cas')
        termin_miesto = request.form.get('termin_miesto')

        if not title or not subject or not level or not termin_miesto:
            flash('Povinné polia musia byť vyplnené', 'danger')
            return redirect(url_for('create_lesson'))

        if termin_miesto == 'SpeedLearn_office' and (not termin_datum or not termin_cas):
            flash('Dátum a čas sú povinné pre miesto SpeedLearn_office.', 'danger')
            return redirect(url_for('create_lesson'))

        # 1. vytvorenie kurzu
        new_lesson = Lesson(
            title = title,
            description = description,
            subject = subject,
            level = level,
            status = 'active',
            created_by = current_user.id,
        )
        db.session.add(new_lesson)
        db.session.flush()   # nove id pre commitom

        # 2. vytvorenie terminu
        new_termin = LessonTermin(
            lesson_id = new_lesson.id,
            datum = termin_datum,
            cas = termin_cas,
            miesto = termin_miesto
        )
        db.session.add(new_termin)

        # 3. Pridanie trenera
        trainer_link = LessonTrainer(lesson_id = new_lesson.id, user_id = current_user.id)
        db.session.add(trainer_link)

        db.session.commit()
        flash('Kurz bol úspešne vytvorený', 'success')
        return redirect(url_for('view_lesson', lesson_id=new_lesson.id))

    return render_template('create_lesson.html')


# zrusenie lesson cez ucitela
@app.route('/lessons/<int:lesson_id>/cancel', methods=['POST'])
@login_required
def cancel_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # over, či aktuálny user je medzi školiteľmi
    is_trainer = LessonTrainer.query.filter_by(
        lesson_id=lesson.id,
        user_id=current_user.id
    ).first()

    if not is_trainer:
        flash('Nemáte oprávnenie zrušiť tento kurz.', 'danger')
        return redirect(url_for('view_lesson', lesson_id=lesson.id))

    lesson.status = 'closed'
    db.session.commit()
    flash('Kurz bol úspešne zrušený.', 'success')
    return redirect(url_for('index'))

# diskusia k lessons
@app.route('/lessons/<int:lesson_id>/discussion', methods=['GET', 'POST'])
@login_required
def lesson_discussion(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # Zoznam účastníkov
    trainer_ids = [lt.user_id for lt in LessonTrainer.query.filter_by(lesson_id=lesson_id).all()]
    student_ids = [sl.student_id for sl in StudentLesson.query.filter_by(lesson_id=lesson_id).all()]
    allowed_user_ids = trainer_ids + student_ids

    # Prístup len pre účastníkov
    if current_user.id not in allowed_user_ids:
        flash('Nemáte prístup k tejto diskusii.', 'danger')
        return redirect(url_for('view_lesson', lesson_id=lesson_id))

    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            # Odošle správu "všetkým" ako kópiu (technicky každému účastníkovi okrem seba)
            for uid in allowed_user_ids:
                new_msg = Message(
                    sender_id=current_user.id,
                    receiver_id=uid,
                    message=content
                )
                db.session.add(new_msg)
            db.session.commit()
            flash('Správa odoslaná.', 'success')
            return redirect(url_for('lesson_discussion', lesson_id=lesson_id))

    # Zobraz len správy medzi účastníkmi
    messages = Message.query.filter(
        Message.sender_id.in_(allowed_user_ids),
        Message.receiver_id.in_(allowed_user_ids)
    ).order_by(Message.sent_at.asc()).all()

    return render_template('lesson_discussion.html', lesson=lesson, messages=messages)

# editovanie sprav
@app.route('/lessons/<int:lesson_id>/messages/<int:message_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_message(lesson_id, message_id):
    message = Message.query.get_or_404(message_id)

    if message.sender_id != current_user.id:
        flash('Nemáte oprávnenie upraviť túto správu.', 'danger')
        return redirect(url_for('lesson_discussion', lesson_id=lesson_id))

    if request.method == 'POST':
        new_message = request.form.get('message')
        if not new_message:
            flash('Správa nesmie byť prázdna.', 'warning')
        else:
            message.message = new_message
            db.session.commit()
            flash('Správa bola upravená.', 'success')
            return redirect(url_for('lesson_discussion', lesson_id=lesson_id))

    return render_template('edit_message.html', lesson_id=lesson_id, message=message)




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
