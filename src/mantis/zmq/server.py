import logging
import zmq

class ZmqServer(object):
    def __init__(self, host: str = "localhost", port: int = 5000):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"tcp://{host}:{port}")
    
    
    

