import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


def main():
    while True:
        # wait for next reqeust from client
        message = socket.recv()
        print("Received requst: %s" % message)

        # Do work 'work'
        time.sleep(1)

        # Send reply back to client
        socket.send(b"World")


if __name__ == "__main__":
    main()
