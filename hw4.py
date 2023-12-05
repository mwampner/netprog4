#!/usr/bin/env python3

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()
import select
import hashlib

import grpc

import csci4220_hw4_pb2
import csci4220_hw4_pb2_grpc

# global variables
dht = []
kv_list = []
node_id = ""
my_port = ""
my_address = ""
k = ""

def print_kbuckets(): # print k-buckets in correct format
    global dht
    for x in range(len(dht)):
        b = str(x) + ":"
        count = k-1
        while count >= 0:
            if(dht[x][count] != ""):
                b = b + " " + str(dht[x][count].id) + ":" + str(dht[x][count].port)
            count = count -1
        print(b)

def xor(id1, id2): # get distance between two ids
    return id1 ^ id2

def find_bucket(dist): # finds bucket based on distance
    num = 0
    for i in range(4):
        if 2**i <= dist and dist < 2**(i+1):
            num = i
            return i

def find_hostname(connect_id): # returns host name based on connect id >=/< 10
    host = "peer"
    if connect_id < 10:
        host = host + "0" + str(connect_id)
    else:
        host = host + str(connect_id)
    return host

def add_node(node): # adds node to most recent spot in dht
    global dht
    bucket = find_bucket(xor(int(node.id), int(node_id)))
    # add node to dht
    if node not in dht[bucket]:
        if dht[bucket][0] == "":
            dht[bucket][0] = node
        else: # shift nodes
            tmp1 = node
            tmp2 = ""
            for y in range(len(dht[bucket])):
                if dht[bucket][y] == "":
                    dht[bucket][y] = tmp1
                    break
                else:
                    tmp2 = dht[bucket][y]
                    dht[bucket][y] = tmp1
                    tmp1 = tmp2
    else: # shift to top spot
        if dht[bucket][0] != node:
            # remove from list so not their twice
            for x in range(len(dht[bucket])):
                if node == dht[bucket][x]:
                    dht[bucket][x] = ""
            tmp1 = node
            tmp2 = ""
            # add node to most recently used
            for x in range(len(dht[bucket])):
                if dht[bucket][x]=="":
                    dht[bucket][x] = tmp1
                    break
                else:
                    tmp2 = dht[bucket][x]
                    dht[bucket][x] = tmp1
                    tmp1 = tmp2
    return

def find_node(dest_id): # Runs FindNode RPC
    global dht
    node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address)

    # start search
    kv = ""
    close_list = []
    visited = []
    closest = ""
    dist = -1
    # Find closest node to destination
    for x in range(len(dht)):
        for y in range(len(dht[x])):
            if(dht[x][y] != "" and (dist == -1 or xor(dht[x][y].id, dest_id) < dist)):
                dist = xor(dht[x][y].id, dest_id)
                closest = dht[x][y]
    visited.append(closest)       
    # submission address
    peer_address = find_hostname(closest.id)
    channel = grpc.insecure_channel(peer_address + ":" + str(closest.port))
    # initial FindNode call
    stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
    kv = stub.FindNode(csci4220_hw4_pb2.IDKey(
        node=node,
        idkey = dest_id
    ))
    channel.close()
    # add nodes to dht
    for x in kv.nodes:
        add_node(x)

    if kv.responding_node.id != dest_id: # value not found and continue
        close_list = kv.nodes
        # add nodes from close_list to dht
        found = False
        for x in close_list: # check if destination was in responding node's k-buckets
            if x.id == dest_id:
                found = True
            add_node(x)
        if not found:
            while kv.responding_node.id != dest_id and len(close_list) != 0:
                for x in visited: # remove visted nodes from closest
                    for y in close_list:
                        if y.id == x.id:
                            close_list.remove(x)
                # run FindNode for all in closelist
                for x in close_list:
                    # submission address
                    peer_address = find_hostname(x.id)
                    channel = grpc.insecure_channel(peer_address + ":" + str(x.port))
                    stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
                    # add all from closelist to visited
                    visited.append(x)
                    kv = stub.FindNode(csci4220_hw4_pb2.IDKey(
                        node=node,
                        idkey = dest_id
                    ))
                    # add nodes to close_list for visiting
                    for y in kv.nodes:
                        close_list.append(y)
                    
                    # remove from close_list
                    close_list.remove(x)
                    # check if value was found
                    if kv.responding_node.id == dest_id:
                        # add nodes to dht
                        add_node(kv.responding_node)
                        for y in kv.nodes:
                            add_node(y)
                        break                
    return kv    

def find_value(key): # calls FindValue RPC
    global dht
    global kv_list
    node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address)

    # start search
    close_list = []
    visited = []
    closest = ""
    dist = -1
    kv = ""
    # search self
    found = False
    for x in kv_list:
        if x.key == key:
            kv = csci4220_hw4_pb2.KV_Node_Wrapper(
                responding_node = node,
                mode_kv=True,
                kv=kv,
                nodes=[]
            )
            found = True
    
    if not found:
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if(dht[x][y] != "" and (dist == -1 or xor(dht[x][y].id, key) < dist)):
                    dist = xor(dht[x][y].id, key)
                    closest = dht[x][y]
        if closest != "": # check for empty k-buckets
            visited.append(closest)
            # submission address
            peer_address = find_hostname(closest.id)
            channel = grpc.insecure_channel(peer_address + ":" + str(closest.port))
            stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
            kv = stub.FindValue(csci4220_hw4_pb2.IDKey(
                node=node,
                idkey = key
            ))
            channel.close()

    if closest != "" and not kv.mode_kv: # value not found
        close_list = kv.nodes
        # add nodes from close_list to dht
        for x in close_list:
            add_node(x)

        while not kv.mode_kv and len(close_list) != 0:
            for x in visited: # remove visted nodes from closest
                if x in close_list:
                    close_list.remove(x)
            # run FindValue for all in closelist
            for x in close_list:
                # submission address
                peer_address = find_hostname(x.id)
                channel = grpc.insecure_channel(peer_address + ":" + str(x.port))
                stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
                # add all from closelist to visited
                visited.append(x)
                kv = stub.FindValue(csci4220_hw4_pb2.IDKey(
                    node=node,
                    idkey = key
                ))
                # add nodes to close_list for visiting
                for x in kv.nodes:
                    close_list.append(x)
                # add nodes to dht
                for x in kv.nodes:
                    add_node(x)
                # check if value was found
                if kv.mode_kv:
                    break   
    return kv

class KadImplServicer(csci4220_hw4_pb2_grpc.KadImplServicer):
    def __init__(self):
        self.node = csci4220_hw4_pb2.Node(
            id=int(node_id), 
            port=int(my_port), 
            address=my_address)
        
    def FindNode(self, idkey, context):
        global dht
        # print message
        print("Serving FindNode(" + str(idkey.idkey) + ") request for " + str(idkey.node.id))
        # add requester to dht
        found = False
        nl = ""
        add_node(idkey.node)

        # check for bootstrap command response
        if idkey.node.id == idkey.idkey:
            closest = {}
            for x in range(len(dht)):
                for y in range(len(dht[x])):
                    if(dht[x][y] != "" and dht[x][y].id != idkey.node.id): # exclude requesting node
                        closest[xor(idkey.idkey, dht[x][y].id)] =  dht[x][y]
            closest = dict(sorted(closest.items()))
            # get k closest
            closest_nodes = []
            count = 0
            for i in closest:
                if count < k:
                    closest_nodes.append(closest[i])
                else:
                    break
            return csci4220_hw4_pb2.NodeList(
                responding_node= self.node,
                nodes = closest_nodes
            )
        # check for node in k-buckets
        return_node = self.node
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if(dht[x][y] != "" and dht[x][y].id == idkey.idkey):
                    return_node = dht[x][y]
        # sort closest_nodes
        closest = {}
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if(dht[x][y] != "" and dht[x][y].id != idkey.node.id): # exclude requesting node
                    closest[xor(idkey.idkey, dht[x][y].id)] =  dht[x][y]
        closest = dict(sorted(closest.items()))
        # get k closest
        closest_nodes = []
        count = 0
        for i in closest:
            if count < k:
                closest_nodes.append(closest[i])
            else:
                break
            count = count + 1
        
        return csci4220_hw4_pb2.NodeList(
            responding_node= return_node,
            nodes = closest_nodes
        )

    def FindValue(self, idkey, context):
        global kv_list
        global dht
        #print message 
        print("Serving FindKey(" + str(idkey.idkey) + ") request for " + str(idkey.node.id))
        # add node to dht
        add_node(idkey.node)
        # check self
        for x in range(len(kv_list)):
            if(idkey.idkey == kv_list[x].key):
                return csci4220_hw4_pb2.KV_Node_Wrapper(
                    responding_node = self.node,
                    mode_kv = True,
                    kv = kv_list[x],
                    nodes = [self.node]
                )        
        # find closest nodes
        closest = {}
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if(dht[x][y] != "" and dht[x][y].id != idkey.node.id): # exclude requesting node
                    closest[xor(idkey.idkey, dht[x][y].id)] =  dht[x][y]
        closest = dict(sorted(closest.items()))
        # get k closest
        closest_nodes = []
        count = 0
        for i in closest:
            if count < k:
                closest_nodes.append(closest[i])
            else:
                break
            count = count +1 

        return csci4220_hw4_pb2.KV_Node_Wrapper(
                    responding_node = self.node,
                    mode_kv = False,
                    nodes = closest_nodes
                )

    def Store(self, KeyValue, context):
        # print message
        print("Storing key " + str(KeyValue.key) + " value \"" + KeyValue.value + "\"")
        # store key
        global kv_list
        # check for existing key/value
        for x in kv_list:
            if x.key == KeyValue.key:
                kv_list.remove(x)
                break
        kv_list.append(KeyValue)
        # add requesting node to dht if not present
        add_node(KeyValue.node)
    
        return csci4220_hw4_pb2.IDKey(
            node = self.node,
            idkey = KeyValue.key
        )

    def Quit(self, IDKey, context):
        # remove quitting node
        global dht
        found = False
        channel = ""
        for x in range(len(dht)):
            for y in range(len(dht[x])):
                if dht[x][y] != "" and dht[x][y].id == IDKey.idkey:
                    dht[x][y] = ""
                    found = True
                    print("Evicting quitting node "+ str(IDKey.idkey) + " from bucket " + str(x))
                    return csci4220_hw4_pb2.IDKey(
                        node = self.node,
                        idkey = IDKey.idkey
                    )
            if found:
                break
        print("No record of quitting node " + str(IDKey.idkey) + " in k-buckets.")
        return
        
def run():  
    if len(sys.argv) != 4:
        print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
        sys.exit(-1)  
    # set up global variables for local node 
    global node_id
    node_id = int(sys.argv[1])
    global my_port
    my_port = str(int(sys.argv[2])) # add_insecure_port() will want a string
    global k
    k = int(sys.argv[3])
    global my_address
    my_address = socket.gethostbyname('localhost')

    # initialize DHT buckets 
    global dht
    for i in range(4):
        dht.append(list())
        for j in range(k):
            dht[i].append("")
    # start grpc server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csci4220_hw4_pb2_grpc.add_KadImplServicer_to_server(
        KadImplServicer(), server
    )
    server.add_insecure_port("[::]:" + str(my_port))
    server.start()
    global kv_list
    while True:
        command = input().strip()
        if command != "": # command input
            if command.startswith("BOOTSTRAP"):
                command = command.split()
                if len(command) != 3:
                    print("Invalid BOOTSTRAP command")
                else:
                    # submission address
                    # connect to node
                    channel = grpc.insecure_channel(command[1] + ":" + command[2])
                    stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
                    # set up node msg
                    node = csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address)
                    # send FindNode
                    close = stub.FindNode(csci4220_hw4_pb2.IDKey(
                        node = node,
                        idkey=int(node_id)
                    ))
                    # add node to k_bucket
                    add_node(close.responding_node)
                    # add closest nodes
                    for x in close.nodes:
                        add_node(x)
                    # print message
                    print("After BOOTSTRAP(" + str(close.responding_node.id) + "), k-buckets are:")
                    print_kbuckets()
                    # close channel
                    channel.close()
                    channel = ""
                    stub = ""
            elif command.startswith("FIND_NODE"):
                command = command.split()
                if len(command) != 2:
                    print("Invalid FIND_NODE command")
                else:
                    print("Before FIND_NODE command, k-buckets are:")
                    print_kbuckets()
                    # check for self find
                    if int(command[1]) == int(node_id):
                        print("Found destination id " + command[1])
                    else: # check for node in k-buckets
                        dest = ""
                        for x in range(len(dht)):
                            for y in range(len(dht[x])):
                                if(dht[x][y] != "" and dht[x][y].id == int(command[1])):
                                    dest = dht[x][y]
                        # search all nodes
                        if dest == "":
                            dest = find_node(int(command[1]))
                        if dest == "": # node not found
                            print("Could not find destination id " + command[1])
                        else: # node found
                            print("Found destination id " + command[1])

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
                        # add to local list
                        kv_list.append(csci4220_hw4_pb2.KeyValue(
                            node =closest,
                            key=int(command[1]),
                            value=command[2]
                        ))
                    else: # send to closer node
                        # submission address
                        peer_address = find_hostname(closest.id)
                        channel = grpc.insecure_channel(peer_address + ":" + str(closest.port))
                        # send to remote node
                        stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
                        stub.Store(csci4220_hw4_pb2.KeyValue(
                            node =csci4220_hw4_pb2.Node(id=int(node_id), port=int(my_port), address=my_address),
                            key=int(command[1]),
                            value=command[2]
                        ))
                        # close new channel
                        channel.close()
                    # print message
                    print("Storing key " + command[1] + " at node " + str(closest.id))
            elif command.startswith("FIND_VALUE"):
                command = command.split()
                if len(command) != 2:
                    print("Invalid FIND_VALUE command")
                else:
                    print("Before FIND_VALUE command, k-buckets are:")
                    print_kbuckets()
                    # check for LOCAL value
                    found = False
                    for x in range(len(kv_list)):
                        if int(command[1]) == kv_list[x].key:
                            print("Found data \"" + kv_list[x].value + "\" for key " + command[1])
                            found = True
                            break
                    # send find_value rpc to closest node
                    if not found:
                        kv = find_value(int(command[1]))
                        if kv == "": # no nodes available for search:
                            print("Could not find key " + command[1])
                        elif kv.mode_kv: # value found
                            print("Found value \"" + kv.kv.value + "\" for key " + command[1])
                        else: # value not foud
                            print("Could not find key " + command[1])
                        
                        # add closest visited nodes to
                        if kv != "": 
                            for x in kv.nodes:
                                add_node(x)
                            # move node to front of list
                            add_node(kv.responding_node)
                    print("After FIND_VALUE command, k-buckets are:")
                    print_kbuckets()
            elif command.startswith("QUIT"):
                # inform known nodes of quit
                for x in range(len(dht)):
                    count = k-1
                    while count >= 0:
                        if dht[x][count] != "":
                            print("Letting " + str(dht[x][count].id) + " know I'm quitting.")
                            
                            try: # send QUIT to nodes in dht
                                # submission address
                                peer_address = find_hostname(dht[x][count].id)
                                channel = grpc.insecure_channel(peer_address + ":" + str(dht[x][count].port))
                                # send quit to node
                                stub = csci4220_hw4_pb2_grpc.KadImplStub(channel)
                                stub.Quit(csci4220_hw4_pb2.IDKey(
                                    node = csci4220_hw4_pb2.Node(id=node_id, port=int(my_port), address=my_address),
                                    idkey=node_id
                                ))
                                channel.close()
                            except: # account for remote node already being closed (they weren't mutually in each others' k-buckets)
                                dht[x][count] = ""
                                break
                        count = count -1
                # shut down self
                print("Shut down node " + str(node_id))
                server.stop(1)
                exit()
            else:
                print("Invalid command")

if __name__ == '__main__':
	run()