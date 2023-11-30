#!/usr/bin/env python3

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()
import select

import grpc

import csci4220_hw4_pb2
import csci4220_hw4_pb2_grpc

dht = {}
node_id = ""
my_port = ""
my_address = ""

def print_kbuckets(buckets):
    for x in buckets:
        b = x + ":"
        for y in buckets[x]:
            b = b + " " + dht[x][y]
        print(b)

def xor(id1, id2):
    return id1 ^ id2

class KadImplServicer(csci4220_hw4_pb2_grpc.KadImplServicer):
    def __init__(self):
        self.node = csci4220_hw4_pb2.Node(
            id=int(node_id), 
            port=int(my_port), 
            address=my_address)
        
    def FindNode(idkey):

        return #(NodeList) 

    def FindValue(IDKey):
        return #(KV_Node_Wrapper)

    def Store(KeyValue):
        return #(IDKey)

    def Quit(IDKey):
        return #(IDKey)


def run():  
    if len(sys.argv) != 4:
        print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
        sys.exit(-1)   

    global node_id
    node_id = int(sys.argv[1])

    global my_port
    my_port = str(int(sys.argv[2])) # add_insecure_port() will want a string
    k = int(sys.argv[3])
    my_hostname = socket.gethostname() # Gets my host name
	#my_address = socket.gethostbyname(my_hostname) # Gets my IP address from my hostname
    global my_address
    my_address = socket.gethostbyname('localhost')

    # initialize DHT buckets 
    global dht
    for i in range(4):
        dht[i] = {}
        for j in range(k):
            dht[i][j] = ""
		
    # start grpc
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csci4220_hw4_pb2_grpc.add_KadImplServicer_to_server(
        KadImplServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("grpc started")
    # select
    inputs = [sys.stdin]
    clients = {}
    stub = ""
    while True:
        readable, _, _ = select.select(inputs, [], [])

        for sock in readable:
            if sock == sys.stdin: # command input
                command = input().strip()
                if command.startswith("BOOTSTRAP"):
                    command = command.split()
                    if len(command) != 3:
                        print("Invalid BOOTSTRAP command")
                    else:
                        # creates a stub
                        #grpc.insecure_channel("localhost:50051")
                        stub = csci4220_hw4_pb2.KadImplStub(grpc.insecure_channel(my_address + ":" + command[2]))
                        # set up node msg
                        node = csci4220_hw4_pb2.Node(id=node_id, port=my_port, address=my_address)
                        # send FindNode
                        remote_node = stub.FindNode(int(node_id))
                        

                elif command.startswith("FIND_NODE"):
                    if len(command) != 2:
                        print("Invalid FIND_NODE command")
                elif command.startswith("STORE"):
                    if len(command) != 2:
                        print("Invalid STORE command")
                elif command.startswith("FIND_VALUE"):
                    if len(command) != 2:
                        print("Invalid FIND_VALUE command")
                elif command.startswith("QUIT"):
                    exit()
                else:
                    print("Invalid command")
        #elif: # message from current connection
        else: # new connection
            print("hello")


	#''' Use the following code to convert a hostname to an IP and start a channel
	#Note that every stub needs a channel attached to it
	#When you are done with a channel you should call .close() on the channel.
	#Submitty may kill your program if you have too many file descriptors open
	#at the same time. '''
	
	#remote_addr = socket.gethostbyname(remote_addr_string)
	#remote_port = int(remote_port_string)
	#channel = grpc.insecure_channel(remote_addr + ':' + str(remote_port))

if __name__ == '__main__':
	run()