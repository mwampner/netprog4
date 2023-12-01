#!/usr/bin/env python3

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()
import select
import hashlib

import grpc

import csci4220_hw4_pb2
import csci4220_hw4_pb2_grpc

dht = []
node_id = ""
my_port = ""
my_address = ""
k = ""

def print_kbuckets():
    global dht
    for x in range(len(dht)):
        b = str(x) + ":"
        for y in range(len(dht[x])):
            if(dht[x][y] != ""):
                b = b + " " + str(dht[x][y].id) + ":" + str(dht[x][y].port)
        print(b)

def xor(id1, id2):
    return id1 ^ id2

def find_bucket(dist):
    num = 0
    for i in range(4):
        if 2**i <= dist and dist < 2**(i+1):
            num = i
            return i

def find_node(stub):
    return
class KadImplServicer(csci4220_hw4_pb2_grpc.KadImplServicer):
    def __init__(self):
        self.node = csci4220_hw4_pb2.Node(
            id=int(node_id), 
            port=int(my_port), 
            address=my_address)
        
    def FindNode(self, idkey, context):
        closest_nodes = [self.node]
        contact_list = [self.node]
        global dht
        # start search
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if dht[x][y] != "" and dht[x][y].id != idkey: # node present and not target node
                    #get distance
                    dist = xor(idkey, dht[x][y].id)
                    # sort closest node list
                    if len(closest_nodes) != 0:
                        for node in closest_nodes:
                            if dist < xor(idkey, node.id):
                                return
                    closest_nodes.append(dht[x][y])
                elif dht[x][y] != "" and dht[x][y].id != idkey: # node present is target node
                    return csci4220_hw4_pb2.NodeList(
                    responding_node= node_id,
                    nodes = closest_nodes[:k]
        )
        return csci4220_hw4_pb2.NodeList(
            responding_node= self.node,
            nodes = closest_nodes
        )

    def FindValue(self, IDKey, context):
        return #(KV_Node_Wrapper)

    def Store(self, KeyValue, context):
        return #(IDKey)

    def Quit(self, IDKey, context):
        return #(IDKey)


def run():  
    if len(sys.argv) != 4:
        print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
        sys.exit(-1)   

    global node_id
    node_id = int(sys.argv[1])

    node_name = ""
    if(node_id < 2):
        node_name = "peer0" + sys.argv[1]
    else:
        node_name = "peer" + sys.argv[1]
    
    # get key for node
    node_key = hash(node_name)
    #m = hashlib.sha1()
    ##m.update(b"This is a str")
    #m.update(b"ring in two parts")
    #m.digest() #Gives the actual hash

    global my_port
    my_port = str(int(sys.argv[2])) # add_insecure_port() will want a string
    global k
    k = int(sys.argv[3])
    my_hostname = socket.gethostname() # Gets my host name
	#my_address = socket.gethostbyname(my_hostname) # Gets my IP address from my hostname
    global my_address
    my_address = socket.gethostbyname('localhost')

    # initialize DHT buckets 
    global dht
    for i in range(4):
        dht.append(list())
        for j in range(k):
            dht[i].append("")
    print("pre-grpc")
    # start grpc
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csci4220_hw4_pb2_grpc.add_KadImplServicer_to_server(
        KadImplServicer(), server
    )
    server.add_insecure_port("[::]:" + str(my_port))
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
                        stub = csci4220_hw4_pb2_grpc.KadImplStub(grpc.insecure_channel(my_address + ":" + command[2]))
                        # set up node msg
                        node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address)
                        # send FindNode
                        close = stub.FindNode(csci4220_hw4_pb2.IDKey(
                            node = node,
                            idkey=int(node_id)
                        ))
                        # add node to k_bucket
                        dist = xor(node_id, close.responding_node.id)
                        bucket = find_bucket(dist)
                        place = False
                        for x in range(len(dht[bucket])):
                            if dht[bucket][x] == "":
                                dht[bucket][x] = close.responding_node
                                place = True
                                break
                            if place:
                                break

                        print("After BOOTSTRAP(" + str(close.responding_node.id) + "), k-buckets are:")
                        print_kbuckets()
                        

                elif command.startswith("FIND_NODE"):
                    command = command.split()
                    if len(command) != 2:
                        print("Invalid FIND_NODE command")
                    else:
                        print("Before FIND_NODE command, k-buckets are:")
                        print_kbuckets()
                        
                        # Run FIND_NODE search

                        print("After FIND_NODE command, k-buckets are:")
                        print_kbuckets()
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
        #else: # new connection
            


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