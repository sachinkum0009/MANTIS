import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")


def main():
    for request in range(10):
        socket.send(b"hello")

        message = socket.recv()
        print("Received reply %s [%s]" % (request, message))


if __name__ == "__main__":
    main()
