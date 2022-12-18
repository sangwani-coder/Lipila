from .auth import login_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint('skoolpay', __name__, url_prefix='/skoolpay')


@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
def dashboard():
    return render_template('school/dashboard.html')
