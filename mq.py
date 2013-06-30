import pika

import config


def create_job(queue, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.rabbit_host))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=message,
                          properties=pika.BasicProperties(
                              delivery_mode=2,
                          ))

    print " [x] Sent in %s: %s" % (queue, message)
    connection.close()
