import random
import mysql.connector
from mysql.connector import Error
import rsa
from re import match
from constants import (
    UserNotExistsError, UserNotLoggedInError, InvalidCredentialsError,
    img_to_binary, decrypt_pass,
    DB_CONFIG, DB_TABLE_STRUCTURE, ALL_DB_TABLES, DB_PKEY, DB_FKEY, DB_HOST, DB_PORT, DB_USER, DB_CHARSET, DB_PASSWORD,
    DB_DATABASE,
    DB_USER_ENCRYPTION_TABLE, DB_USER_PROFILE_TABLE,
    DB_MERCHANT_ENCRYPTION_TABLE, DB_MERCHANT_PROFILE_TABLE,
    DB_USER_TRANSACTION_HISTORY_TABLE, DB_MERCHANT_TRANSACTION_HISTORY_TABLE,
    PATH_DEFAULT_PIC,
    TABLE_EMAIL, TABLE_USERNAME, TABLE_REGID, TABLE_MERCHANTNAME,
    YES, NO,
    OCAT_FOOD_AND_BEVERAGE, OCAT_DAIRY_AND_GROCERIES
)


class TempUser:
    def __init__(self):
        self.fname:    str = ''
        self.uname:    str = ''
        self.email:    str = ''
        self.regid:    str = ''
        self.password: str = ''
        self.random_usernames = []

    def load_random_names(self):
        first_name, last_name = self.fname.split() if len(self.fname.split()) > 1 else [self.fname, '']
        if len(last_name) < 1:
            for i in range(30):
                self.random_usernames.append(first_name + str(random.randint(1, 99999)))
                self.random_usernames.append(first_name[0] + str(random.randint(1, 99999)))
        else:
            for i in range(15):
                self.random_usernames.append(first_name + last_name + str(random.randint(1, 99999)))
                self.random_usernames.append(last_name + first_name + str(random.randint(1, 99999)))
                self.random_usernames.append(last_name[0] + first_name + str(random.randint(1, 99999)))
                self.random_usernames.append(first_name[0] + last_name + str(random.randint(1, 99999)))


class User:
    """ User class to bridge frontend and backend. """

    def __init__(self):
        self.database = None
        self.is_logged_in:          bool = False
        self.fname:                  str = ''
        self.uname:                  str = ''
        self.email:                  str = ''
        self.regid:                  str = ''
        self.uID:                    str = ''
        self.phone:                  str = ''
        self.profilepic:           bytes = b''
        self.is_email_verified:      str = NO
        self.is_transaction_enabled: str = NO

    def get_transaction_history(self, index=0, rows=10):
        return self.database.execute_query(
            f"SELECT * FROM {self.database.db_config[DB_USER_TRANSACTION_HISTORY_TABLE]} "
            f"WHERE username=%s ]"
            f"LIMIT {index},{rows};",
            self.uname
        )[0]

    def transaction(self):
        pass

    def set_email_verified(self):
        """ Sets email verified as True in the DB and the current User object """
        if self.is_logged_in:
            self.database.execute_query("UPDATE profiledata SET is_email_verified=%s WHERE uID=%s", YES, self.uID)
            self.database.connection.commit()
        else:
            raise UserNotLoggedInError

    def set_login(self, uname: str, email: str, regid: str, fname: str, uID: str, profile_pic: bytes,
                  phone_no: str, is_email_verified: str, is_transaction_enabled: str):
        self.fname = fname
        self.uname = uname
        self.email = email
        self.regid = regid
        self.uID = uID
        self.phone = phone_no
        self.profilepic = profile_pic
        self.is_email_verified = is_email_verified
        self.is_transaction_enabled = is_transaction_enabled
        self.is_logged_in = True

    def set_nfc_serial(self, serial: str):
        self.database.execute_query(
            f"UPDATE {DB_USER_PROFILE_TABLE} "
            f"SET nfc_serial_no=%s "
            f"WHERE username='{self.uname}'", serial
        )


class TempMerchant:
    def __init__(self):
        self.mname: str = ''

        self.password: str = ''


class Merchant:
    """ Merchant class to bridge frontend and backend """
    def __init__(self):
        self.database = None
        self.is_logged_in:     bool = False
        self.mname:             str = ''
        self.email:             str = ''
        self.mID:               str = ''
        self.phone:             str = ''
        self.outlet:            str = ''
        self.category:          str = ''
        self.profilepic:      bytes = b''
        self.is_email_verified: str = NO

    def set_email_verified(self):
        """ Sets email verified as TRUE in the database as well as current merchant object """
        pass

    def set_login(self, mname: str, email: str, mID: str, profilepic: bytes, phone: str, outlet: str, category: str,
                  is_email_verified: str):
        self.mname = mname
        self.email = email
        self.mID = mID
        self.profilepic = profilepic
        self.phone = phone
        self.outlet = outlet
        self.category = category
        self.is_email_verified = is_email_verified
        self.is_logged_in = True


class DataBase(object):
    """
    Database class for operations on MySQL database for:
        - encryptions
        - history of payments, etc
    """

    def __init__(self, user_obj: User, merchant_obj: Merchant, **db_config):
        """
        Initialize database connection and cursor

        :param user_obj: `User` class object for login
        :param db_config: configuration dict for the database
        """
        self.db_config = db_config
        self.user_logged_in = False
        self.user_obj = user_obj
        self.user_obj.database = self
        self.merchant_logged_in = False
        self.merchant_obj = merchant_obj
        self.merchant_obj.database = self

        try:
            self.connection = mysql.connector.connect(host=self.db_config[DB_HOST], port=self.db_config[DB_PORT],
                                                      user=self.db_config[DB_USER], charset=self.db_config[DB_CHARSET],
                                                      password=decrypt_pass(self.db_config[DB_PASSWORD]))
            self.cursor = self.connection.cursor()
        except Error as e:
            print(e)

        self.check_existence()

    def add_new_merchant(self, merchantname: str, email: str, password: str, phone_no: str, outletname: str,
                         category: str, pic: bytes = PATH_DEFAULT_PIC):
        """
        Adds a new merchant to the database

        :param merchantname: unique merchantname
        :param email: merchant's email
        :param password: a valid merchant password
        :param phone_no: a valid 10 digit phone number
        :param outletname: full name of the outlet as in
        :param category: category of merchant outlet type (includes: Food and Beverage, Stationaries, etc)
        :param pic: bytearray object of merchant's pic
        :return: None
        """
        pub_key, pri_key = rsa.newkeys(512)
        enc_pwd = rsa.encrypt(password.encode(), pub_key)

        self.execute_query(
            f'INSERT INTO {self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]} VALUES(%s,%s,%s,%s,%s,%s,%s,%s);',
            merchantname, email, *list(map(str, [
                pri_key.n, pri_key.e, pri_key.d, pri_key.p, pri_key.q
            ])), enc_pwd
        )
        self.connection.commit()
        self.execute_query(f'INSERT INTO {self.db_config[DB_MERCHANT_PROFILE_TABLE]} VALUES(%s,%s,%s,%s,%s,%s,%s);',
                           merchantname, self.generate_mID(), pic, phone_no, outletname, category, NO)
        self.connection.commit()

    def add_new_user(self, username: str, email: str, regid: str, password: str, fullname: str, phone_no: str,
                     nfc_serial_no: str = '', pic: bytes = PATH_DEFAULT_PIC):
        """
        Adds a new user to the database

        :param username: unique username
        :param email: valid user's institutional email
        :param regid: valid user registration ID
        :param password: a valid user password
        :param fullname: full name of the user
        :param phone_no: a valid 10 digit phone number
        :param nfc_serial_no: serial key of the NFC card
        :param pic: bytearray object of user's pic
        :return: None
        """
        pub_key, pri_key = rsa.newkeys(512)
        enc_pwd = rsa.encrypt(password.encode(), pub_key)

        self.execute_query(
            f'INSERT INTO {self.db_config[DB_USER_ENCRYPTION_TABLE]} VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);',
            username, email, regid, *list(map(str, [
                pri_key.n, pri_key.e, pri_key.d, pri_key.p, pri_key.q
            ])), enc_pwd
        )
        self.execute_query(f'INSERT INTO {self.db_config[DB_USER_PROFILE_TABLE]} VALUES(%s,%s,%s,%s,%s,%s,%s,%s);',
                           username, self.generate_uID(), pic, fullname, phone_no, nfc_serial_no, NO, NO)
        self.connection.commit()

    def check_duplicate(self, email: str, regid: str):
        if len(self.execute_query(
            'SELECT email, regid FROM userencryptiondata WHERE email=%s OR regid=%s;', email, regid
        )) >= 1:
            return True
        return False

    def check_duplicate_username(self, username: str):
        if len(self.execute_query(
            "SELECT username FROM userencryptiondata WHERE username=%s;", username
        )) >= 1:
            return True
        return False

    def check_existence(self):
        """ Checks if required Database and Tables exist """
        self.execute_query(f"CREATE DATABASE IF NOT EXISTS {self.db_config[DB_DATABASE]};")
        self.connection.database = self.db_config['database']
        for table in ALL_DB_TABLES:
            self.execute_query(self.create_table_query(table))

    def check_merchant_login(self, merchantkey: str, merchantpass: str):
        """
        Checks if entered credentials match the ones in database

        :param merchantkey: userkey can be unique username, email or registration ID
        :param merchantpass: password to be validated
        :return: true if password correct else false
        """
        merchantkey_type = TABLE_EMAIL
        if merchantkey.startswith("@"):
            merchantkey_type = TABLE_MERCHANTNAME
            merchantkey = merchantkey[1:]

        try:
            n, e, d, p, q, passwd = self.execute_query(
                f"SELECT n,e,d,p,q,PASSWORD "
                f"FROM {self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]} "
                f"WHERE {merchantkey_type}='{merchantkey}'"
            )[0]
            if rsa.decrypt(passwd, rsa.PrivateKey(*list(map(int, [n, e, d, p, q])))).decode() == merchantpass:
                self.merchant_obj.set_login(*self.get_merchant_login_data(merchantkey_type, merchantkey))
                return True
            else:
                raise InvalidCredentialsError(f'Invalid credentials for: "{merchantkey}"')
        except IndexError:
            raise UserNotExistsError(f'User does not exist for: "{merchantkey}"')

    def check_user_login(self, userkey: str, userpass: str) -> bool:
        """
        Checks if entered credentials match the ones in database

        :param userkey: userkey can be unique username, email or registration ID
        :param userpass: password to be validated
        :return: true if password correct else false
        """
        userkey_type = TABLE_REGID
        if userkey.startswith("@"):
            userkey_type = TABLE_USERNAME
            userkey = userkey[1:]
        elif match("[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+", userkey):
            userkey_type = TABLE_EMAIL

        try:
            n, e, d, p, q, passwd = self.execute_query(
                f"SELECT n,e,d,p,q,PASSWORD "
                f"FROM {self.db_config[DB_USER_ENCRYPTION_TABLE]} "
                f"WHERE {userkey_type}='{userkey}'"
            )[0]
            if rsa.decrypt(passwd, rsa.PrivateKey(*list(map(int, [n, e, d, p, q])))).decode() == userpass:
                self.user_obj.set_login(*self.get_user_login_data(userkey_type, userkey))
                return True
            else:
                raise InvalidCredentialsError(f'Invalid credentials for: "{userkey}"')
        except IndexError:
            raise UserNotExistsError(f'User does not exist for: "{userkey}"')

    def close(self):
        """ Disconnect MySQL server """
        self.connection.close()

    @classmethod
    def create_table_query(cls, table):
        """
        Creates the query for adding table to database using table_structure JSON file

        :param table: table name for which the query has to be created
        :return: `str` object for table creation query
        """
        columns = DB_TABLE_STRUCTURE[table]['columns']
        keys = DB_TABLE_STRUCTURE[table]['key_constraints']
        primary = f"{DB_PKEY}({keys[DB_PKEY]})" if len(keys[DB_PKEY]) > 1 else ''
        foreign = ','.join([
            f"{DB_FKEY}({keys[DB_FKEY][i]['name']}) REFERENCES {j}"
            for i in range(len(keys[DB_FKEY]))
            for j in keys[DB_FKEY][i]["references"]
        ]) if len(keys[DB_FKEY]) > 0 else ""
        if foreign != '' and primary != '':
            primary += ','
        return f"CREATE TABLE IF NOT EXISTS {DB_TABLE_STRUCTURE[table]['table_name']}(" + \
            f",".join([" ".join(column.values()) for column in columns]) + "," + \
            primary + foreign + ');'

    def execute_query(self, query: str, *args) -> list:
        """
        Executes MySQL query and displays its result

        :param query: SQL query to be executed
        :param args: SQL query arguments
        :returns: result of the SQL query -> tuple[tuple]
        """
        self.cursor.execute(query, tuple(args))
        return self.cursor.fetchall()

    def get_merchant_login_data(self, merchantkey_type, merchant_key):
        """

        :param merchantkey_type:
        :param merchant_key:
        :return:
        """
        return self.execute_query(
            f"SELECT "
            f"{self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]}.merchantname,"
            f"{self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]}.email,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.mID,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.pic,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.phone_no,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.outletname,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.category,"
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.is_email_verified "
            f"FROM {self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]} "
            f"INNER JOIN {self.db_config[DB_MERCHANT_PROFILE_TABLE]} "
            f"ON {self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]}.merchantname="
            f"{self.db_config[DB_MERCHANT_PROFILE_TABLE]}.merchantname "
            f"AND {self.db_config[DB_MERCHANT_ENCRYPTION_TABLE]}.{merchantkey_type}='{merchant_key}';"
        )[0]

    def get_user_login_data(self, userkey_type, userkey):
        """
        Gets all the display-able details for the specified user using userkey

        :param userkey_type: includes email, username, regid
        :param userkey: key value for any of the key types
        :return: `tuple` containing user details
        """
        return self.execute_query(
            f"SELECT "
            f"{self.db_config[DB_USER_ENCRYPTION_TABLE]}.username,"
            f"{self.db_config[DB_USER_ENCRYPTION_TABLE]}.email,"
            f"{self.db_config[DB_USER_ENCRYPTION_TABLE]}.regid,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.fullname,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.uID,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.pic,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.phone_no,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.is_email_verified,"
            f"{self.db_config[DB_USER_PROFILE_TABLE]}.is_transaction_enabled "
            f"FROM {self.db_config[DB_USER_ENCRYPTION_TABLE]} "
            f"INNER JOIN {self.db_config[DB_USER_PROFILE_TABLE]} "
            f"ON {self.db_config[DB_USER_ENCRYPTION_TABLE]}.username={self.db_config[DB_USER_PROFILE_TABLE]}.username "
            f"AND {self.db_config[DB_USER_ENCRYPTION_TABLE]}.{userkey_type}='{userkey}';"
        )[0]

    def generate_mID(self):
        """
        Generates a random mID for the merchant between 12-16 characters in length.
        :return: merchant ID string
        """
        mIDs = self.execute_query(f'SELECT mID FROM {self.db_config[DB_MERCHANT_PROFILE_TABLE]};')
        mID = 'MID_' + str(random.randrange(100000000000, 9999999999999999))
        while mID in mIDs:
            mID = 'MID_' + str(random.randrange(100000000000, 9999999999999999))
        else:
            return "MID_" + str(mID)

    def generate_uID(self):
        """
        Generates a random uID for the user between 12-16 characters in length.
        :return: user ID string
        """
        uIDs = self.execute_query(f'SELECT uID FROM {self.db_config[DB_USER_PROFILE_TABLE]};')
        uid = 'UID_' + str(random.randrange(100000000000, 9999999999999999))
        while uid in uIDs:
            uid = 'UID_' + str(random.randrange(100000000000, 9999999999999999))
        else:
            return uid

    def is_connected(self) -> bool:
        """ Check if connection timed out """
        return self.connection.is_connected()


if __name__ == '__main__':
    u = User()
    m = Merchant()
    db = DataBase(user_obj=u, merchant_obj=m, **DB_CONFIG)
    user_test_data = [
        ('prerakl123', 'pp7432@srmist.edu.in', 'RA2111026010394', 'Prerack@123', img_to_binary('static/img/t1.png'),
         'Prerak Lodha', '9829778167', '79:e8:99:5d'),
        ('shubhyboi', 'sm4269@srmist.edu.in', 'RA2111026010420', 'Shubhy@456', img_to_binary('static/img/t2.jpg'),
         'Shubhankar Mishra', '9274917548', ''),
        ('njnemda', 'nj2910@srmist.edu.in', 'RA2111026010408', 'njulka@789', img_to_binary('static/img/t3.jpg'),
         'Nimish Julka', '9683648502', ''),
        ('aryonsutta', 'aj4820@srmist.edu.in', 'RA2111026010373', 'ajsutta@294', img_to_binary('static/img/t4.jpg'),
         'Aryan Jaiswal', '7896284901', ''),
        ('dipila4467', 'dp4299@srmist.edu.in', 'RA2314002698444', 'bigpapa69', img_to_binary('static/img/t5.png'),
         'Dilip Anand', '8592048275', ''),
        ('harshalAMD', 'ha4812@srmist.edu.in', 'RA0029948779812', 'hamad!!2', img_to_binary('static/img/t6.jpeg'),
         'Harsad Ahmad', '6924705812', ''),
        ('GOVIpro', 'gp2348@srmist.edu.in', 'RA110984499577', 'abcdefgh', img_to_binary('static/img/t7.png'),
         'Govind Prakash', '7214857191', ''),
        ('kdevi2004', 'kd1234@srmist.edu.in', 'RA1099870059987', 'kd04@333', img_to_binary('static/img/t8.jpeg'),
         'Kamal Devi', '9784289012', ''),
        ('DcoolMishra', 'da9302@srmist.edu.in', 'RA111480210908', 'dmcoolboi', img_to_binary('static/img/t9.png'),
         'Dekisuki Mishra', '9495967262', ''),
        ('nchau007', 'nc1929@srmist.edu.in', 'RA0002889567710', 'naunau3217', img_to_binary('static/img/t10.jpeg'),
         'Nyan Chau', '8969594432', '')
    ]

    merchant_test_data = [
        ('tajking', 'tajking@gmail.com', 'tjk$3456', img_to_binary('static/img/t10.jpeg'), 'Taj King', '8723564871',
         OCAT_FOOD_AND_BEVERAGE),
        ('ckolkata', 'kolkatachat@gmail.com', 'kolCHAAT24178', img_to_binary('static/img/t9.png'), 'Kolkata Chat',
         '7653821955', OCAT_FOOD_AND_BEVERAGE),
        ('pcollections', 'princesscollection@gmail.com', 'pc@921', img_to_binary('static/img/t8.jpeg'),
         'Princess Collection', '9764529156', OCAT_DAIRY_AND_GROCERIES),
        ('pJuices', 'pricessjuices@gmail.com', 'Pj@5497', img_to_binary('static/img/t7.png'), 'Princess Juices',
         '9568212465', OCAT_FOOD_AND_BEVERAGE),
        ('durgaswamy', 'durgaswamy@gmail.com', 'durga%100', img_to_binary('static/img/t6.jpeg'),
         'Durgaswamy Supermarket', '9357905849', OCAT_DAIRY_AND_GROCERIES),
        ('milan', 'milanrestaurants@gmail.com', 'mrestS*128947', img_to_binary('static/img/t5.png'), 'Milan',
         '8671923648', OCAT_FOOD_AND_BEVERAGE),
        ('sunnydays', 'sunnydays@gmail.com', 'sdayFOODS', img_to_binary('static/img/t4.jpg'),
         'Sunny Days - SRM University Food Court', '6987292346', OCAT_FOOD_AND_BEVERAGE),
        ('subway', 'contact@subway.com', 'SUBSUBSUB', img_to_binary('static/img/t3.jpg'), 'Subway', '8769823467',
         OCAT_FOOD_AND_BEVERAGE),
        ('Emo', 'emo@gmail.com', 'EMOemo51315', img_to_binary('static/img/t2.jpg'), 'Emo', '9477891234',
         OCAT_FOOD_AND_BEVERAGE),
        ('mdBiryani', 'biryanimahal@gmail.com', 'AWFh124o09@#@#', img_to_binary('static/img/t1.png'),
         'MD Biryani Mahal', '8947128971', OCAT_FOOD_AND_BEVERAGE),
    ]

    for un, em, rid, pwd, ppic, fn, phno, nfc_serial in user_test_data:
        db.add_new_user(username=un, fullname=fn, email=em, regid=rid, password=pwd, phone_no=phno,
                        nfc_serial_no=nfc_serial, pic=ppic)

    for mn, em, pwd, ppic, ol, phno, cat in merchant_test_data:
        db.add_new_merchant(merchantname=mn, email=em, password=pwd, phone_no=phno, outletname=ol, category=cat,
                            pic=ppic)

    # print(db.execute_query('SELECT username,fullname FROM profiledata;'))
    print(db.check_user_login('@shubhyboi', "Shubhy@456"))
    print(db.check_user_login('aj4820@srmist.edu.in', "ajsutta@294"))
    print(db.check_user_login('RA2111026010394', "Prerack@123"))
    print(db.check_merchant_login('contact@subway.com', 'SUBSUBSUB'))
    print(db.check_merchant_login('@milan', 'mrestS*128947'))
    print(db.get_user_login_data(TABLE_EMAIL, 'aj4820@srmist.edu.in'))
    print(db.get_merchant_login_data(TABLE_MERCHANTNAME, 'milan'))
    # print(db.execute_query("SELECT e.username,p.username,e.email FROM encryptiondata e INNER JOIN profiledata p ON "
    #                        "e.username=p.username and e.email='pp7432@srmist.edu.in';"))
    # print(db.get_user_login_data(TABLE_REGID, 'RA2111026010394'))
    print(db.check_duplicate('milan', 'RA2111026010393'))
    db.close()
    
