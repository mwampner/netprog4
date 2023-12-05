Helper Functions
	print_kbuckets(): uses global dht variable to print k-buckets in
		correct format for output
	xor(id1,id2): returns id1^id2
	find_bucket(dist): takes distance between two ids and finds what
		bucket they belong in
	find_hostname(connect_id): returns node hostname based on if 
		connect_id is greater than or equal to 10 or less than
		10
	add_node(node): takes in a Node and adds it the the open
		most recently used spot in global dht 
		(moving nodes down or out when
		necessary, including its own previous location) 
	find_node(dest_id): handles FindNode() calls; finds the closest available
		node to the dest_id and calls FindNode() on it. If it is the
		correct node or the correct node is in its k-buckets the
		function returns the correct node along with the closest 
		nodes. If not, then it starts the algorithm to search for
		the correct node.
	find_value(key): starts by checking if the key is stored locally;
		if not, it searches the next closest nodes. it continues
		the search until all possible nodes have been visited or
		the key is found

KadImpleServicer RPCs
	FindNode(): first checks if FindNode() is being used in Bootstrap
		command, adds requester to self, and returns closest nodes 
		to requesting node; searches for node in k-buckets if 
		regular FindNode() call and returns destination node
		as responding node if it was found
	FindValue(): returns KV_Node_Wrapper with mode_kv = True if key
		is found locally, if not finds k closest nodes and returns
		KV_Node_Wrapper with mode_kv = False
	Store(): appends KeyValue object to local list and removes
		old KeyValue object if it has the same key
	Quit(): removes requesting node from k-buckets if it is found

run() structure
	Initializes dht to handle k-buckets and storing nodes and starts
	listening on the specified port and begins to accept commands

	BOTSTRAP connects to the specified remote node and calls Find_Node
	and adds the responding node and its closest nodes to dht
	
	FIND_NODE checks if it is looking for itself then checks its k-
	buckets. If it is not found in either of those it calls helper
	function find_node()

	STORE first checks if it is the closest node id to the key and
	stores it locally if true. if not, it sends a request to the 
	closest remote node

	FIND_VALUE checks if value is stored locally and if not it 
	calls the find_value() helper function

	QUIT sends the Quit() rpc to all nodes in its k-buckets; it 
	excepts error in the case of a remote node having already shut
	down before the local node, but only the local node had the remote
	node in its k-buckets while the remote node did not have the 
	local node
	
