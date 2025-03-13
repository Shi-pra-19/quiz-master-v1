from flask import Blueprint
from flask_login import login_user, login_required, current_user, logout_user
from flask import Flask, redirect, url_for, render_template, request, flash

admin = Blueprint("admin", __name__)

@admin.route('/home')
@login_required
def home():
    return render_template('admin_home.html')

