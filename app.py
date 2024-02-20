from flask import Flask, render_template, request, redirect
import mysql.connector as mysql
import pika, sys, os
import asyncio
import ast
app = Flask(__name__)

mydb = mysql.connect(
database="sprzedaz",
host="host.docker.internal",
user="root",
password="secret",
port="3306"
)


@app.route("/remove",methods=["GET","POST"])
def remove():
    mycursor = mydb.cursor()
    if request.method == "POST":
        number = int(request.form.get("id"))
        sql = "DELETE from sprzedaze where lp =%s"
        val = (number,)
        mycursor.execute(sql,val)
        mydb.commit()
    return redirect("/")

@app.route("/remove2",methods=["GET","POST"])
def remove2():
    connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@rabbitmq:5672"))
    channel = connection.channel()
    channel.queue_declare(queue='server',durable=True)
    if request.method == "POST":
        number = int(request.form.get("id"))
        sql = f"DELETE from zakupy where lp={number}"
        channel.basic_publish(exchange='', routing_key='server',body=sql)
    return redirect("/")


@app.route("/add",methods=["GET","POST"])
def add():
    mycursor = mydb.cursor()
    if request.method == "POST":
        name = request.form.get("name")
        item = request.form.get("item")
        pay = request.form.get("pay")
        sql = "insert into sprzedaze (name,item,pay) values(%s,%s,%s)"
        val = (name,item,pay)
        mycursor.execute(sql,val)
        mydb.commit()
    return redirect("/")

@app.route("/add2",methods=["GET","POST"])
def add2():
    connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@rabbitmq:5672"))
    channel = connection.channel()
    channel.queue_declare(queue='server',durable=True)
    
    if request.method == "POST":
        name = request.form.get("name")
        item = request.form.get("item")
        pay = request.form.get("pay")
        sql = f"INSERT INTO zakupy (name, item, pay) VALUES ({name}, {item}, {pay})"
        channel.basic_publish(exchange='', routing_key='server',body=sql)

    return redirect("/")

a = ""
async def listen():
        global a
        connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@rabbitmq:5672"))
        channel = connection.channel()
        
        channel.queue_declare(queue='listener',durable=True)
        def callback(ch, method, properties, body):
            global a
            print(f" [x] Received {body}")
            a = body
            connection.close()

        channel.basic_consume(queue='listener', on_message_callback=callback, auto_ack=True)

        print(' [*] Waiting for messages.')
        channel.start_consuming()
        return a

@app.route('/')
async def index():
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS sprzedaze (lp INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(255), item VARCHAR(255), pay int)")
    mycursor.execute("SELECT * FROM sprzedaze")
    result = []
    for x in mycursor:
        result.append(x)
    connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@rabbitmq:5672"))
    channel = connection.channel()
    channel.queue_declare(queue='server',durable=True)
    channel.basic_publish(exchange='', routing_key='server',body="select * from zakupy")
    result2 = await listen()
    result2 = ast.literal_eval(str(result2)[2:-1].replace("\\",""))
    print(result2)
    return render_template('index.html', result=result,result2=result2)