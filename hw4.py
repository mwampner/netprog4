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
kv_list = []
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
        global dht
        # print message
        print("Serving FindNode(" + str(idkey.node.id) + ") request for " + str(idkey.idkey))
        # add requester to dht
        found = False
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if dht[x][y] != "" and dht[x][y].id == idkey.node.id:
                    found = True
                    break
            if found:
                break
        if not found:
            bucket = xor(self.node.id, idkey.node.id)
            for y in range(len(dht[bucket])):
                if dht[bucket][y] == "":
                    dht[bucket][y] = idkey.node
                    break
        
        closest_nodes = [self.node]
        contact_list = [self.node]
        
        # start search
        #for x in range(len(dht)):
        #    for y in range(len(dht[x])):
        #        if dht[x][y] != "" and dht[x][y].id != idkey.node.id: # node present and not target node
        #            #get distance
        #            dist = xor(idkey, dht[x][y].id)
        #            # sort closest node list
        #            if len(closest_nodes) != 0:
        #                for node in closest_nodes:
        #                    if dist < xor(idkey, node.id):
        #                        return
        #            closest_nodes.append(dht[x][y])
        #        elif dht[x][y] != "" and dht[x][y].id != idkey: # node present is target node
        #            if len(closest_nodes) >= k:
        #                closest_nodes = closest_nodes[:k]
        #            return csci4220_hw4_pb2.NodeList(
        #            responding_node= node_id,
        #            nodes = closest_nodes
        #)
        return csci4220_hw4_pb2.NodeList(
            responding_node= self.node,
            nodes = closest_nodes
        )

    def FindValue(self, IDKey, context):
        global kv_list
        # check self
        for x in range(len(kv_list)):
            if(IDKey.idkey == kv_list[x].key):
                return csci4220_hw4_pb2.KV_Node_Wrapper(
                    responding_node = self.node,
                    mode_kv = True,
                    kv = kv_list[x],
                    nodes = [self.node]
                )
                break
        return 

    def Store(self, KeyValue, context):
        # print message
        print("Storing key " + str(KeyValue.key) + " value \"" + KeyValue.value + "\"")
        # store key
        global kv_list
        kv_list.append(KeyValue)
        # add requesting node to dht if not present
        global dht
        bucket = find_bucket(xor(self.node.id, KeyValue.node.id))
        for x in range(len(dht[bucket])):
            if dht[bucket][x] != "" and dht[bucket][x].id != KeyValue.node.id:
                dht[bucket][x] = KeyValue.node
                break
            elif dht[bucket][x] != "" and dht[bucket][x].id != KeyValue.node.id:
                break
        return csci4220_hw4_pb2.IDKey(
            node = self.node,
            idkey = KeyValue.key
        )

    def Quit(self, IDKey, context):
        # remove quitting node
        global dht
        found = False
        
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if dht[x][y] != "" and dht[x][y].id == IDKey.idkey:
                    dht[x][y] = ""
                    found = True
                    print("Evicting quitting node "+ str(IDKey.idkey) + " from bucket " + str(x))
                    break
            if found:
                break
        return csci4220_hw4_pb2.IDKey(
            node = self.node,
            idkey = IDKey.idkey
        )


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
    # start grpc
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csci4220_hw4_pb2_grpc.add_KadImplServicer_to_server(
        KadImplServicer(), server
    )
    server.add_insecure_port("[::]:" + str(my_port))
    server.start()
    # variables
    inputs = [sys.stdin]
    clients = {}
    stub = ""
    channel = ""
    stubs = {}
    boot = {}
    global kv_list
    while True:
        command = input().strip()
        if command != "": # command input
            
            if command.startswith("BOOTSTRAP"):
                command = command.split()
                if len(command) != 3:
                    print("Invalid BOOTSTRAP command")
                else:
                    # creates a stub
                    #grpc.insecure_channel("localhost:50051")
                    if channel != "":
                        channel.close()
                    channel = grpc.insecure_channel(my_address + ":" + command[2])
                    stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
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
                    stubs[close.responding_node.id] = stub 
                    boot[close.responding_node.id] = channel
                    for x in range(len(dht[bucket])):
                        if dht[bucket][x] == "":
                            dht[bucket][x] = close.responding_node
                            place = True
                            break
                        if place:
                            break
                    # print message
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
                command = command.split()
                if len(command) != 3:
                    print("Invalid STORE command")
                else:
                    closest = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address)
                    dist = xor(closest.id, int(command[1]))
                    # check dht for closer node
                    for x in range(len(dht)):
                        for y in range(len(dht[x])):
                            if dht[x][y] != "":
                                if(xor(dht[x][y].id, int(command[1])) < dist):
                                    dist = xor(dht[x][y].id, int(command[1]))
                                    closest = dht[x][y]
                    # check for self being closest
                    if closest.id == int(node_id):
                        kv_list.append(csci4220_hw4_pb2.KeyValue(
                            node =closest,
                            key=int(command[1]),
                            value=command[2]
                        ))
                    else: # send to closer node
                        kv = csci4220_hw4_pb2.KeyValue(
                            node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address),
                            key=int(command[1]),
                            value=command[2]
                        )
                        if closest.id in stubs.keys(): # check for current stub
                            stubs[closest.id].Store(csci4220_hw4_pb2.KeyValue(
                                node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address),
                                key=int(command[1]),
                                value=command[2]
                            ))
                        else: # create new stub
                            channel2 = grpc.insecure_channel(my_address + ":" + str(closest.port))
                            stub2 = csci4220_hw4_pb2_grpc.KadImplStub()
                            stub2.Store(csci4220_hw4_pb2.KeyValue(
                                node =closest,
                                key=int(command[1]),
                                value=command[2]
                            ))
                            # close new channel
                            channel2.close()
                    # print message
                    print("Storing key " + command[1] + " at node " + str(closest.id))

            elif command.startswith("FIND_VALUE"):
                command = command.split()
                if len(command) != 2:
                    print("Invalid FIND_VALUE command")
                else:
                    # check for value
                    found = False
                    for x in range(len(kv_list)):
                        if int(command[1]) == kv_list[x].key:
                            print("Found data \"" + kv_list[x].value + "\" for key " + command[1])
                            found = True
                            break
                    # send find_value rpc
                    if not found:
                        kv = stub.FindValue(csci4220_hw4_pb2.IDKey(
                            node = csci4220_hw4_pb2.Node(id=node_id, port=int(my_port), address=my_address),
                            idkey=int(command[1])
                        ))
                        if kv.mode_kv: # value found
                            print("Found value \"" + kv.kv.value + "\" for key " + command[1])
                        else: # value not foud
                            print("Could not find key " + command[1])


                    print("After FIND_VALUE command, k-buckets are:")
                    print_kbuckets()
            elif command.startswith("QUIT"):
                # inform known nodes of quit
                for x in range(len(dht)):
                    for y in range(len(dht[x])):
                        if dht[x][y] != "":
                            if len(boot) > 0 and dht[x][y].id in boot.keys():
                                stubs[dht[x][y].id].Quit(csci4220_hw4_pb2.IDKey(
                                    node = csci4220_hw4_pb2.Node(id=node_id, port=int(my_port), address=my_address),
                                    idkey=node_id
                                ))
                            else:
                                print(dht[x][y])
                                channel2 = grpc.insecure_channel(my_address + ":" + str(dht[x][y].port))
                                stub2 = csci4220_hw4_pb2_grpc.KadImplStub(channel2)
                                stub2.Quit(csci4220_hw4_pb2.IDKey(
                                    node = csci4220_hw4_pb2.Node(id=node_id, port=int(my_port), address=my_address),
                                    idkey=node_id
                                ))
                                channel2.close()

                # shut down self
                print("Shut down node " + str(node_id))
                if channel != "":
                    channel.close()
                server.stop(1)
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