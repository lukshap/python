# coding: UTF-8
import yaml, mysql
import mysql.connector
from mysql.connector import errorcode
import random
import hashlib
from string import ascii_letters, digits
#y  = yaml.load("config.yml")

with open("config.yaml") as conf:
    y = yaml.load(conf)


def gen_salt():
    salt=''
    seq = ascii_letters+digits
    for i in range(0, 10):
        salt+=random.choice(seq)
    return salt

def get_hash_password(password):
    salt = gen_salt()
    hash1 = hashlib.sha1(salt.encode()).hexdigest().encode()
    hash2 = hashlib.sha1(salt.encode()+password.encode()).hexdigest().encode()
    password_hash = hashlib.sha1(hash1+hash2).hexdigest()
    return salt, password_hash

def get_hash_password_reverse(password, salt):
    hash1 = hashlib.sha1(salt.encode()).hexdigest().encode()
    hash2 = hashlib.sha1(salt.encode()+password.encode()).hexdigest().encode()
    password_hash = hashlib.sha1(hash1+hash2).hexdigest()
    return password_hash

def find_user(login, password, con):
        try:
            cur = con.cursor()
            str = "select login, password, salt from users where login = '" + login + "';"
            cur.execute(str)
            data = cur.fetchone()
            print(data)
            if data == None:
                return "User does not exist."
            salt = data[2]
            hash_password = get_hash_password_reverse(password, salt)
            if hash_password == data[1]:
                return "User is found."
            else:
                return "Login or password is not correct."
        except mysql.connector.Error as err:
            print(err)
        else:
            con.close()

if __name__ == "__main__":
    try:
        con = mysql.connector.connect(user=y['mysql']['login'], password=y['mysql']['password'], database = y['mysql']['database'], host=y['mysql']['host'], port=y['mysql']['port'], autocommit=True)
        cur = con.cursor()
        st = "DROP database " + y['mysql']['database'] + ";"
        cur.execute(st)
        st = "create database " + y['mysql']['database'] + ";"
        cur.execute(st)
        st = "use " + y['mysql']['database'] + ";"
        cur.execute(st)
        st = "create table goods(good_id int auto_increment primary key, name varchar(60) not null, cost double not null, description text, img blob);"
        cur.execute(st)
        st = "create table users(user_id int auto_increment primary key, login varchar(60) unique not null, password varchar(90) not null, role tinyint default 0, salt varchar(10), balans double not null default 0);"
        cur.execute(st)
        st = "create table orders(order_id int auto_increment primary key, total_cost double, date timestamp, user_id int, foreign key(user_id) references users(user_id));"
        cur.execute(st)
        st = "create table goods_in_order(order_id int, good_id int, amount int, foreign key(order_id) references orders(order_id), foreign key(good_id) references goods(good_id));"
        cur.execute(st)

        st = "insert into goods(name, cost, description, img) values ('Платье', '3', 'Apart', './Images/dress1.gif');"
        cur.execute(st)
        st = "insert into goods(name, cost, description,img) values ('Блузка', '2', 'Broadway', './Images/blouse1.gif');"
        cur.execute(st)
        st = "insert into goods(name, cost, description, img) values ('Блузка', '5', 'Mango', './Images/blouse2.gif');"
        cur.execute(st)
        st = "insert into goods(name, cost, description, img) values ('Юбка', '6', 'Mango', './Images/skirt.gif');"
        cur.execute(st)
        st = "insert into goods(name, cost, description, img) values ('Костюм', '7', 'Top Secret', './Images/suit.gif');"
        cur.execute(st)

        data = get_hash_password("qwerty")
        salt = data[0]
        password = data[1]
        st = "insert into users(login, role, salt, password, balans) values ('Alex', 1, '" + salt + "',  '" + password + "', 100.5"  ");"
        cur.execute(st)
        data = get_hash_password("12345")
        salt = data[0]
        password = data[1]
        st = "insert into users(login, role, salt, password) values ('Ivan', 1, '" + salt + "',  '" + password + "');"
        cur.execute(st)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
           print(err)
    else:
        con.close()
