import pika, sys, os
import asyncio
import psycopg
connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@rabbitmq:5672"))
listening = connection.channel()
sending = connection.channel()
        
listening.queue_declare(queue='server',durable=True)
sending.queue_declare(queue="listener",durable=True)
def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    with psycopg.connect("host=host.docker.internal dbname=postgres user=user password=secret") as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS zakupy (lp SERIAL PRIMARY KEY, name VARCHAR(255), item VARCHAR(255), pay int)")
            request = str(str(body)[2:-1])
            print(request)
            conn.commit()
            if(request.split(" ")[0].upper()=="SELECT"):
                cursor.execute(request)
                record = cursor.fetchall()
                print(record)
                sending.basic_publish(exchange='', routing_key='listener',body=str(record))
            elif(request.split(" ")[0].upper()=="INSERT"):
                sql = request.lower().split("values")[0] + "values (%s, %s,%s)"
                cursor.execute(sql,(request.lower().split("values")[1].replace(" ","")[1:-1].split(",")[0],request.lower().split("values")[1].replace(" ","")[1:-1].split(",")[1],request.lower().split("values")[1].replace(" ","")[1:-1].split(",")[2]))
                conn.commit()
            else:
                cursor.execute(request)
                conn.commit()



listening.basic_consume(queue='server', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages.')
listening.start_consuming()

