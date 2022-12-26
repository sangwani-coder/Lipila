from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    send_file
)

import os
from skoolpay.db import get_db, current_app
from skoolpay.helpers import generate_pdf

from skoolpay.momo.momo import Momo
from skoolpay.momo.mtn_momo import MTN
from skoolpay.momo.airtel_momo import Airtel

bp = Blueprint('skoolpay', __name__, url_prefix='/skoolpay')


# a simple page that says hello
@bp.route('/', methods = ['GET', 'POST'])
def homepage():
    # return "Index"
    session.clear()
    if request.method == 'POST':
        session.clear()
        student = request.form['student']
        return redirect(url_for('skoolpay.get_student_data', id=student))
    return render_template('payment/index.html')


@bp.route('payment/<id>', methods = ['GET', 'POST'])
def get_student_data(id):
    db = get_db()
    error = None

    if request.method == 'GET':
        student =  db.execute('SELECT * FROM student WHERE id=?',(id,)).fetchone()

        if student is None:
            error = 'No student found!'
        if error is None:
            flash('Confirm student details')
            school_id = db.execute('SELECT school FROM student WHERE id=?',(id,)).fetchone()
            school = db.execute('SELECT school FROM school WHERE id=?',(school_id['school'],)).fetchone()

            session['user-id'] = int(id)
            session['firstname'] = student['firstname']
            session['lastname'] = student['lastname']
            session['school'] = school['school']
            session['tuition'] = student['tuition']
            session['student'] = student['firstname'] + ' ' + student['lastname']
            session['school-id'] = school_id['school']

            return render_template('payment/confirm.html', student=student, school=school['school'])
    flash(error)
    return render_template('payment/index.html')

    
@bp.route('/confirmed', methods = ['GET', 'POST'])
def confirmed():
    # return "Index"
    if request.method == 'GET':
        data = {
            # 'amount':session['amount'],
            # 'account':session['account'],
            'id':session['user-id'],
            'fname':session['firstname'],
            'lname':session['lastname'],
            'school':session['school'],
            'tuition':session['tuition']
            }
        return render_template('payment/confirmed.html', data=data)

    amount = request.form['amount']
    account = request.form['mobile']
    if not amount:
        flash('amount missing')
        student = {'firstname':session['firstname'], 'lastname':session['lastname']}
        return render_template('payment/confirm.html', student=student, school=session['school'])
    elif not account:
        flash('account missing')
        student = {'firstname':session['firstname'], 'lastname':session['lastname']}
        return render_template('payment/confirm.html', student=student, school=session['school'])
    else:
        nets = Momo()
        net = nets.get_network(account)
        if net =='mtn':
            session['account'] = account
        elif net =='airtel':
            session['account'] = account
        else:
            session['account'] = 'None'
        session['amount'] = int(amount)
        

    return redirect(url_for('skoolpay.payment'))

@bp.route('/payment', methods=['GET', 'POST'])
def payment():

    partyId = str(session['account'])
    user = str(session['user-id'])
    amount = str(session['amount'])
    externalId = '12346'

    error =  None
        
    if request.method == 'GET':
        net = Momo().get_network(partyId)

        if net == 'mtn' or net == 'airtel':
            session['net'] = net
        else:
            session['net'] = None
            flash('Failed to verify account')
            student = {'firstname':session['firstname'], 'lastname':session['lastname']}
            return render_template('payment/confirm.html', student=student, school=session['school'])
        student = {'firstname':session['firstname'], 'lastname':session['lastname']}
        return render_template('payment/confirm.html', student=student, school=session['school'])
    
    if session['net'] == 'mtn':
        sp = MTN()
        payment = sp.request_to_pay(amount, partyId, externalId)
        if payment.status_code == 200:
            db = get_db()
            db.execute("INSERT INTO payment (student_id, amount, school, account_number) \
                VALUES(?,?,?,?)",(user, amount, session['school-id'], partyId),
                )

            payment = db.execute(
                "SELECT * FROM payment WHERE student_id=?",(user,)
            ).fetchone()

            student = db.execute(
                "SELECT * FROM student WHERE id=?",(user,)
            ).fetchone()
            db.commit()

            names =  student['firstname'] + ' ' + student['lastname']

            msg = 'success payment of' + ' ' + str(payment['amount']) + ' for' + ' ' + names
            
            flash(msg)
    
    elif session['net'] == 'airtel':
        sp = Airtel()
        payment = sp.make_payment(amount, partyId)
        if payment.status_code == 200:
            db = get_db()
            db.execute("INSERT INTO payment (student_id, amount, school, account_number) \
                VALUES(?,?,?,?)",(user, amount, session['school-id'], partyId),
                )
                
            payment = db.execute(
                "SELECT * FROM payment WHERE student_id=?",(user,)
            ).fetchone()

            student = db.execute(
                "SELECT * FROM student WHERE id=?",(user,)
            ).fetchone()
            db.commit()
            names =  student['firstname'] + ' ' + student['lastname']

            msg = 'success payment of' + ' ' + str(payment['amount']) + ' for' + ' ' + names
            
            flash(msg)
    else:
        error = 'An Error occured! Failed to Make Payment'
        flash(error)
    return redirect(url_for('skoolpay.show_history'))

@bp.route('/history', methods=['GET', 'POST'])
def show_history():
    db = get_db()

    user = session['user-id']

    payment = db.execute(
        "SELECT * FROM payment WHERE student_id=?",(user,)
    ).fetchall()

    return render_template('payment/history.html', school=session['school'], data=payment)


@bp.route('/download/<receipt>', methods=['GET', 'POST'])
def download(receipt):
    """ downloads a pdf receipt"""
    db = get_db()
    path = current_app.root_path

    data = db.execute('SELECT * FROM payment WHERE id=?',(receipt,)).fetchone()
    rec = generate_pdf(data)
    file_path = os.path.join(path, rec).replace('\\', '/')
  

    return render_template('payment/download.html', id=receipt, file_path=file_path)