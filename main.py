"""
Resources:
Icons: https://iconscout.com/unicons/explore/line
Flask Docs: https://flask.palletsprojects.com/en/2.2.x/
Jinja Docs: https://jinja.palletsprojects.com/en/3.1.x/
"""


# #################################################################################################################### #
# ################################################# IMPORT LIBRARIES ################################################# #
# #################################################################################################################### #

import json
from flask import Flask, render_template, request, redirect, url_for
from db import DataBase, User, TempUser, Merchant, TempMerchant
from constants import (
    CURRENT_YEAR, WS_CODES,
    PATH_IMAGE_DIR,
    DB_CONFIG,
    UserNotExistsError, InvalidCredentialsError
)

# #################################################################################################################### #
# ###################################################### WEB APP ##################################################### #
# #################################################################################################################### #
tempuser = TempUser()
user = User()
tempmerchant = TempMerchant()
merchant = Merchant()
database = DataBase(user_obj=user, merchant_obj=merchant, **DB_CONFIG)
app = Flask(__name__, static_folder='./static')
app.config['UPLOAD_FOLDER'] = PATH_IMAGE_DIR


#                ######################                  #
#                ###### DB_USER #######                  #
#                ######################                  #


@app.route('/')
def root_page():
    return redirect('/signin')


@app.route('/signup/<code>')
@app.route('/signup', methods=('GET', 'POST'))
def signup(code: str = ''):
    """ Return sign-up template """
    kwarg_dict = {
        "TITLE": "Register Tap-a-Tap",
        "CODE": code,
        "CODE_MSG": WS_CODES[code] if code != '' else '',
        "CURRENT_YEAR": CURRENT_YEAR
    }
    return render_template('register.html', **kwarg_dict)


@app.route('/register/<code>')
@app.route('/register', methods=('GET', 'POST'))
def register(code: str = ''):
    """ Method to call after sign-up form fill-up """
    if request.method == 'POST':
        tempuser.fname = request.form.get('r-fname')
        tempuser.email = request.form.get('r-iemail')
        tempuser.regid = request.form.get('r-rid')
        tempuser.password = request.form.get('r-password')

        if database.check_duplicate(email=tempuser.email, regid=tempuser.regid) is True:
            return redirect('/signup/ACC_AAE')
        tempuser.load_random_names()

        kwarg_dict = {
            "USERNAME_LIST": json.dumps(tempuser.random_usernames),
            "CODE": code,
            "CODE_MSG": WS_CODES[code] if code != '' else '',
            "CURRENT_YEAR": CURRENT_YEAR
        }

        return render_template('username.html', **kwarg_dict)
    return '<h2>Access to private data of website denied!</h2>'


@app.route('/signup_successful', methods=('GET', 'POST'))
def signup_successful():
    if request.method == 'POST':
        uname = request.form.get('r-uname')
        if database.check_duplicate_username(uname) is True:
            return redirect('/register/ACC_UAE')
        if uname.isalnum():
            tempuser.uname = uname
            database.add_new_user(tempuser.uname, tempuser.email, tempuser.regid, tempuser.password, tempuser.fname, '')
            return redirect('/signin/ACC_SCFL')
    else:
        return '<h2>Access to private data of website denied!</h2>'


@app.route('/signin/<code>')
@app.route('/signin', methods=('GET', 'POST'))
def signin(code=''):
    if user.is_logged_in:
        return redirect(f'/user/{user.uID}')
    CODE_MSG = WS_CODES[code] if code != '' else ''
    kwarg_dict = {
        "TITLE": "Sign-In Tap-a-Tap",
        'CODE': code,
        'CODE_MSG': CODE_MSG,
        "CURRENT_YEAR": CURRENT_YEAR
    }
    return render_template('register.html', **kwarg_dict)


@app.route('/fetch', methods=('GET', 'POST'))
def fetch():
    userkey = request.form.get('s-userkey')
    userpass = request.form.get('s-userpass')
    try:
        if database.check_user_login(userkey, userpass):
            return redirect(f'/user/{user.uID}')
    except InvalidCredentialsError:
        return redirect('/signin/ACC_IC')
    except UserNotExistsError:
        return redirect('/signin/ACC_DNE')


@app.route('/reset_password')
def reset_password():
    kwarg_dict = {
        "CURRENT_YEAR": CURRENT_YEAR
    }
    return render_template('password_reset.html', **kwarg_dict)


@app.route('/user/<string:uID>')
def home_page(uID: str):
    # if not user.is_logged_in:
    #     return redirect('/signin')
    #
    # if user.uID != uID:
    #     return redirect('/signin/ACC_SIE')

    kwarg_dict = {
        "CURRENT_YEAR": CURRENT_YEAR,
        "FULL_NAME": user.fname,
        "TABLE_USERNAME": user.uname,
        "TABLE_EMAIL": user.email,
        "TABLE_REGID": user.regid,
        "PHONE_NO": user.phone,
        "IS_EMAIL_VERIFIED": user.is_email_verified,
        "IS_TRANSACTION_ENABLED": user.is_transaction_enabled,
        "USERID": uID,
        "user": user
    }
    return render_template('home.html', **kwarg_dict)


@app.route('/user/<string:uID>/profile')
def display_profile(uID: str):
    # if not user.is_logged_in and user.uID != uID:
    #     return redirect('/signin')
    kwarg_dict = {
        "CURRENT_YEAR": CURRENT_YEAR,
        "FULL_NAME": user.fname,
        "TABLE_USERNAME": user.uname,
        "TABLE_EMAIL": user.email,
        "TABLE_REGID": user.regid,
        "PHONE_NO": user.phone,
        "IS_EMAIL_VERIFIED": user.is_email_verified,
        "IS_TRANSACTION_ENABLED": user.is_transaction_enabled,
        "USERID": uID,
        "user": user
    }
    return render_template('profile.html', **kwarg_dict)


@app.route('/user/<string:uID>/editprofile')
def edit_profile(uID: str):
    # if not user.is_logged_in:
    #     return redirect('/signin')
    kwarg_dict = {
        "CURRENT_YEAR": CURRENT_YEAR,
        "FULL_NAME": user.fname,
        "TABLE_USERNAME": user.uname,
        "TABLE_EMAIL": user.email,
        "TABLE_REGID": user.regid,
        "PHONE_NO": user.phone,
        "IS_EMAIL_VERIFIED": user.is_email_verified,
        "IS_TRANSACTION_ENABLED": user.is_transaction_enabled,
        "USERID": uID,
        "user": user
    }
    return render_template('editprofile.html', **kwarg_dict)


@app.route('/user/<string:uID>/transaction_history')
def transaction_history(uID: str):
    kwarg_dict = {
        "CURRENT_YEAR": CURRENT_YEAR,
        "user": user
    }
    return render_template('history.html', **kwarg_dict)


@app.route('/user/<string:uID>/connect_card')
def connect_card(uID: str):
    # if not user.is_logged_in:
    #     return redirect('/signin')

    kwarg_dict = {
        "user": user,
        "CURRENT_YEAR": CURRENT_YEAR
    }
    return render_template('connect_card.html', **kwarg_dict)


#                ######################                  #
#                ###### MERCHANT ######                  #
#                ######################                  #


@app.route('/msignup', methods=('GET', 'POST'))
def msignup():
    pass


@app.route('/mregister', methods=('GET', 'POST'))
def mregister():
    pass


@app.route('/msignup_successful', methods=('GET', 'POST'))
def msignup_successful():
    pass


if __name__ == '__main__':
    # run the app
    app.run(host='0.0.0.0')
