import datetime
import os
from json import load


class UserNotExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserNotLoggedInError(Exception):
    pass


def get_db_json(path) -> dict:
    """
    :param path: file path for DB configuration JSON file
    :return: type `dict` for database configuring kwargs
    """
    return load(open(path))


def img_to_binary(filename: str) -> bytes:
    """
    Get image in binary base64 form
    :param filename: path for the image file
    :return: binary image data
    """
    return open(filename, 'rb').read()


def encrypt_pass(password: str) -> str:
    """
    Encrypts password from string to binary
    :param password: password to be encrypted
    :return: encrypted string
    """
    return ''.join([bin(ord(i)) for i in password])


def decrypt_pass(encoded: str) -> str:
    """
    Decrypts password from binary to string
    :param encoded: binary or encoded password string
    :return: decoded string
    """
    return ''.join([chr(int('0b'+i, 2)) for i in encoded.split('0b')[1:]])


# CURRENT YEAR FOR COPYRIGHT
CURRENT_YEAR:  int = datetime.datetime.now().year


# WEBSITE CODES AND MSGs
WS_CODES: dict = {
    'ACC_AAE': 'Account Already Exists!',
    'ACC_DNE': 'Account Does Not Exist!',
    'ACC_IC':  'Invalid Credentials!',
    'ACC_SIE': 'Sign-in to access contents!',
    'ACC_SCFL': 'Account Successfully Created!',
    'ACC_UAE': 'Username Already Exists!'
}


# DB_DATABASE RELATED CONSTANTS
DB_INIT_JSON:                          str = 'db/db_init.json'
DB_CONFIG:                            dict = get_db_json(DB_INIT_JSON)
DB_TABLE_JSON:                         str = 'db/db_table_structure.json'
DB_TABLE_STRUCTURE:                   dict = get_db_json(DB_TABLE_JSON)
DB_USER_ENCRYPTION_TABLE:              str = 'user_encryption_table'
DB_USER_PROFILE_TABLE:                 str = 'user_profile_table'
DB_USER_TRANSACTION_HISTORY_TABLE:     str = 'user_transaction_history_table'
DB_USER_TEST_ACCOUNT_TABLE:            str = 'user_account_table'
DB_MERCHANT_ENCRYPTION_TABLE:          str = 'merchant_encryption_table'
DB_MERCHANT_PROFILE_TABLE:             str = 'merchant_profile_table'
DB_MERCHANT_TRANSACTION_HISTORY_TABLE: str = 'merchant_transaction_history_table'
DB_MERCHANT_TEST_ACCOUNT_TABLE:        str = 'merchant_account_table'
ALL_DB_TABLES:                        list = [DB_USER_ENCRYPTION_TABLE, DB_MERCHANT_ENCRYPTION_TABLE,
                                              DB_USER_PROFILE_TABLE, DB_MERCHANT_PROFILE_TABLE,
                                              DB_USER_TRANSACTION_HISTORY_TABLE, DB_MERCHANT_TRANSACTION_HISTORY_TABLE,
                                              DB_USER_TEST_ACCOUNT_TABLE, DB_MERCHANT_TEST_ACCOUNT_TABLE]
DB_PKEY:                               str = 'PRIMARY KEY'
DB_FKEY:                               str = 'FOREIGN KEY'
DB_HOST:                               str = 'host'
DB_PORT:                               str = 'port'
DB_USER:                               str = 'user'
DB_CHARSET:                            str = 'charset'
DB_PASSWORD:                           str = 'password'
DB_DATABASE:                           str = 'database'


# PATH AND IMAGE RELATED CONSTANTS
PATH_IMAGE_DIR:     str = os.path.join('static', 'img')
PATH_DEFAULT_PIC: bytes = img_to_binary('static/img/defaultdp.jpg')


# DB_USER AND MERCHANT DATA RELATED CONSTANTS
TABLE_EMAIL:        str = 'email'
TABLE_USERNAME:     str = 'username'
TABLE_REGID:        str = 'regid'
TABLE_MERCHANTNAME: str = 'merchantname'
TABLE_UID:          str = 'uID'
TABLE_MID:          str = 'mID'


# `is_condition` TYPE CONSTANTS
YES: str = 'YES'
NO:  str = 'NO'


# MERCHANT OUTLET CATEGORY TYPE CONSTANTS
OCAT_FOOD_AND_BEVERAGE:   str = 'Food and Beverage'
OCAT_DAIRY_AND_GROCERIES: str = 'Dairy and Groceries'
OCAT_STATIONARIES:        str = 'Stationaries'
OCAT_PHARMACEUTICAL:      str = 'Pharmaceutical'
OCAT_OTHERS:              str = 'Others'


# e = encrypt_pass('Prerack@123')
# d = decrypt_pass(e)
# print(e)
# print(d)
