
# coding=utf-8
#------------------------------------------------------------------------------------------------------
# TDA596 Labs - Server Skeleton
# server/server.py
# Input: Node_ID total_number_of_ID
# Student Group: 15
# Student names: Henrik Möller & Mikael Matero
#------------------------------------------------------------------------------------------------------
# We import various libraries
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler # Socket specifically designed to handle HTTP requests
import sys # Retrieve arguments
import re
from random import randint
from time import sleep
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management

#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
board_frontpage_footer_template = "server/board_frontpage_footer_template.html"
board_frontpage_header_template = "server/board_frontpage_header_template.html"
boardcontents_template = "server/boardcontents_template.html"
entry_template = "server/entry_template.html"

#------------------------------------------------------------------------------------------------------
# Static variables definitions
PORT_NUMBER = 80
#------------------------------------------------------------------------------------------------------




#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class BlackboardServer(HTTPServer):
#------------------------------------------------------------------------------------------------------
	def __init__(self, server_address, handler, vessel_id, vessel_list):

	        # We call the super init
		HTTPServer.__init__(self,server_address, handler)
                # we create the dictionary of values
		self.store = {}
		# We keep a variable of the next id to insert
		self.current_key = -1
		# our own ID (IP is 10.1.0.ID)
		self.vessel_id = vessel_id
		# The list of other vessels
		self.vessels = vessel_list
                # Number of nodes
                self.num_vessels = len(self.vessels)
                # Current leader at this time in election, initialized to self
                self.current_leader = (self.vessel_id, randint(0,self.num_vessels*200))
                # Set true if this vessel is elected leader
                self.is_leader = False
                # Create string of next ip for election
                self.target_ip = "10.1.0.%s" % ((self.vessel_id % self.num_vessels) + 1)
                
                # Wait for nodes to initialize, then initiate leader election and add own results to election list
                # Run leader election in thread so that the election can be delayed without blocking the server
                thread = Thread(target=self.init_election,args=[self.target_ip])
		thread.daemon = True
		thread.start()


#------------------------------------------------------------------------------------------------------
        def init_election(self, target):
                sleep(1)
                print "Init: Vessel %s trying to contact vessel %s" % (self.vessel_id, (self.vessel_id % self.num_vessels) + 1)
                self.contact_vessel(target, "/leader_election/init/", str(self.vessel_id), str(self.current_leader[1]))

#------------------------------------------------------------------------------------------------------
	# We add a value received to the store
	def add_value_to_store(self, value):
		# We add the value to the store
                print("Added value %s with index %d" % (value,self.current_key+1))
                self.current_key += 1
                self.store[self.current_key] = value

#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
	def modify_value_in_store(self,key,value):
		# we modify a value in the store if it exists
                try:
                        print("Modified stored value at index %d from %s to %s" % (key,self.store[key],value))
                        self.store[key]=value
                except KeyError:
                        print("Key %d not present when modifying in vessel %d" % (key,self.vessel_id))

#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,key):
		# we delete a value in the store if it exists
		try:
                        print("Deleted value stored at key [%d] from store" % (key))
                        del self.store[key]
                except Exception as e:
                        print("Error while deleting key %d from vessel %d" % (key,self.vessel_id))
                        print(e)

#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, key, value):                
		# the Boolean variable we will return
		success = False
		# The variables must be encoded in the URL format, through urllib.urlencode.
                # The variables passed to another vessel depend on the specified path in the function call
                post_content = ""      
                if "delete" in path:
		        post_content = urlencode({key : value, "delete" : 1})
                elif "modify" in path:
                        post_content = urlencode({key : value, "delete" : 0})
                elif "election" in path:
                        post_content = urlencode({key : value, "elect" : "e"})
                else:
                        post_content = urlencode({key : value})

		# the HTTP header must contain the type of data we are transmitting, here URL encoded
		headers = {"Content-type": "application/x-www-form-urlencoded"}
		# We should try to catch errors when contacting the vessel
		try:
			# We contact vessel:PORT_NUMBER since we all use the same port
			# We can set a timeout, after which the connection fails if nothing happened
                        connection = HTTPConnection("%s:%d" % (vessel_ip, PORT_NUMBER), timeout = 30)
			# We only use POST to send data (PUT and DELETE not supported)
			action_type = "POST"
			# We send the HTTP request
			connection.request(action_type, path, post_content, headers)
                       	# We retrieve the response
			response = connection.getresponse()
                       	# We want to check the status, the body should be empty
			status = response.status
                       	# If we receive a HTTP 200 - OK
			if status == 200:
				success = True
                # We catch every possible exceptions
		except Exception as e:
			print "Error while contacting %s" % vessel_ip
			# printing the error given by Python
			print(e)

		# we return if we succeeded or not
		return success
#------------------------------------------------------------------------------------------------------
	# We send a received value to all the other vessels of the system
	def propagate_value_to_vessels(self, path, key, value):
		# We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				# A good practice would be to try again if the request failed
				# Here, we do it only once.
				self.contact_vessel(vessel, path, key, value)		
#------------------------------------------------------------------------------------------------------




#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST request
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class BlackboardRequestHandler(BaseHTTPRequestHandler):
#------------------------------------------------------------------------------------------------------
	# We fill the HTTP headers
	def set_HTTP_headers(self, status_code = 200):
		 # We set the response status code (200 if OK, something else otherwise)
		self.send_response(status_code)
		# We set the content type to HTML
		self.send_header("Content-type","text/html")
		# No more important headers, we can close them
		self.end_headers()
#------------------------------------------------------------------------------------------------------
	# a POST request must be parsed through urlparse.parse_QS, since the content is URL encoded
	def parse_POST_request(self):
		post_data = ""
		# We need to parse the response, so we must know the length of the content
		length = int(self.headers['Content-Length'])
		# we can now parse the content using parse_qs
		post_data = parse_qs(self.rfile.read(length), keep_blank_values=1)
		# we return the data
		return post_data
#------------------------------------------------------------------------------------------------------ 
#------------------------------------------------------------------------------------------------------
# Request handling - GET
# This function contains the logic executed when this server receives a GET request
# This function is called AUTOMATICALLY upon reception and is executed as a thread!
#------------------------------------------------------------------------------------------------------
	def do_GET(self):
		#print("Receiving a GET on path %s" % self.path)
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)

                # Build the complete html document piece by piece
                html_page = ""
                # Board header
	        with open(board_frontpage_header_template) as html_file:
                        html_page = html_file.read()
                # For each entry stored, create a partial html file containing
                # information about all stored entries
                html_entries = ""
                for entry in self.server.store:
                        with open(entry_template) as html_file:
                                tmp = html_file.read()
                                html_entries += tmp % ("entries/"+str(entry),entry,self.server.store[entry])
                # Use the partial file from the for loop above when building upon the html document
                with open(boardcontents_template) as html_file:
                        html_page += html_file.read() % ("Entries",html_entries)
                # Board footer
                with open(board_frontpage_footer_template) as html_file:
                        html_page += html_file.read()
                # HTML file is completed
                self.wfile.write(html_page)

#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
                self.set_HTTP_headers(200)

                # Parse the post request and store it in a dict
                post_data = self.parse_POST_request()
                # The operations are added to the path so that all clients can determine the correct
                # action for this POST. The path combined with the POST body is used when determining
                # the action.
                # An entry is stored in post_data as such: {'entry': ['sven']}
                # The path to add a value to index 0 is: /entries/0
                # If message is a leader election message, continue with election
                if "elect" in post_data:
                        self.do_election(post_data)
                else:
                        entry_nr = ""
                        # Parse entry number from message path
                        if "delete" in post_data:
                                entry_nr =  re.search('[\d]+', self.path).group()
                        # Path is set to a value depending on post_data
                        self.path = self.change_path(post_data,entry_nr)
                        # Process message (and propagate if vessel is leader)
                        if self.server.is_leader:
                                self.handle_post_data(post_data,entry_nr)
                                self.propagate(post_data)
                        # If not leader, check if msg came from leader and either process msg or send to leader
                        else:
                                if "from_leader" in self.path:
                                        self.handle_post_data(post_data,entry_nr)
                                else:
                                        self.send_to_leader(post_data)
                                        
#------------------------------------------------------------------------------------------------------
# Selects the correct operation to perform depending on the path
#------------------------------------------------------------------------------------------------------
        def handle_post_data(self,post_data,entry_nr):
                if "delete" in self.path:
                        self.delete(post_data,entry_nr)
                elif "modify" in self.path:
                        self.modify(post_data,entry_nr)
                elif "entry" in post_data:
                        self.add(post_data)

#------------------------------------------------------------------------------------------------------
# Delete entry
#------------------------------------------------------------------------------------------------------
        def delete(self,post_data,entry_nr):
                self.server.delete_value_in_store(int(entry_nr))
                
#------------------------------------------------------------------------------------------------------
# Modify entry
#------------------------------------------------------------------------------------------------------
        def modify(self,post_data,entry_nr):
                self.server.modify_value_in_store(int(entry_nr),post_data["entry"][0])
                        
#------------------------------------------------------------------------------------------------------
# Add entry
#------------------------------------------------------------------------------------------------------
        def add(self,post_data):
                self.server.add_value_to_store(post_data["entry"][0])

#------------------------------------------------------------------------------------------------------
# Perform leader election in a ring. Nodes send their randomly generated integer (rank) to the next
# node in the ring. When a node receives a leader election message, it compares the received rank
# to the highest rank (received so far), and if the new rank is higher, it sends that value forward.
# When the node that had the highest initial rank receives its rank, it knows that the value has
# propagated throughout the ring, and it has won the election. Thus all nodes have the same leader.
# We purposely omitted the "c" message, as it does not serve any purpose (thus far) in our implementation.
# For further discussion on this topic, we refer to our report.
#------------------------------------------------------------------------------------------------------
        def do_election(self,post_data):
                self.path = "/leader_election/"
                keys = post_data.keys()
                new_id = keys[0]
                # Since dicts are unordered, pick the correct key
                if new_id == 'elect':
                        new_id = keys[1] 
                new_rank = post_data[new_id][0]
                forward_new_leader = False

                # If a node receives its own id in the message, it knows it has acquired leadership
                if self.server.vessel_id == int(new_id):
                        print "Leader election done, leader is %s with number %s" % (new_id, new_rank)
                        self.server.is_leader = True
                        print "I won!"
                # Break the tie if two vessels have the same rank
                elif int(self.server.current_leader[1]) == int(new_rank) \
                     and self.server.vessel_id < new_id:
                        forward_new_leader = True
                # Else, compare the received rank with rank of current leader, and forward the new
                # rank if it is higher than the rank of the current leader
                elif int(self.server.current_leader[1]) < int(new_rank):
                        self.server.current_leader = (new_id,new_rank)
                        forward_new_leader = True

                if forward_new_leader:
                        thread = Thread(target=self.server.contact_vessel,args=\
                                        (self.server.target_ip,\
                                         self.path,\
                                         new_id,\
                                         new_rank))
		      	thread.daemon = True
		        thread.start()

                        print "New leader is %s with number %s " %\
                                (self.server.current_leader[0], self.server.current_leader[1] )

#------------------------------------------------------------------------------------------------------
# Propagate a received value to the network (only used by leader)
#------------------------------------------------------------------------------------------------------
        def propagate(self,post_data):
                print "leader propagating value ", post_data["entry"][0]
		thread = Thread(target=self.server.propagate_value_to_vessels,args=\
                                ("/from_leader" + self.path,\
                                 "entry",\
                                 post_data["entry"][0]))
		thread.daemon = True
		thread.start()

#------------------------------------------------------------------------------------------------------
# If a node that isn't leader receives a message from the board, send this message to be processed
# by the leader before making changes to the stored values for consistent data in the system.
#------------------------------------------------------------------------------------------------------
        def send_to_leader(self,post_data):
                print "sending %s to leader" % (post_data["entry"][0])
		thread = Thread(target=self.server.contact_vessel,args=\
                                        ("10.1.0.%s" % self.server.current_leader[0],\
                                         self.path,\
                                         "entry",\
                                         post_data["entry"][0]))
		thread.daemon = True
		thread.start()

#------------------------------------------------------------------------------------------------------
# Change the path of the packet depending on the post_data contents, unless it is a message from the
# leader (in which case the path has already been modified prior to being received by this node).
#------------------------------------------------------------------------------------------------------
        def change_path(self,post_data,entry_nr):
                if "from_leader" in self.path:
                        return self.path
                if "delete" in post_data:
                        if post_data["delete"][0] == "0":
                                return "/modify/"+entry_nr
                        else:
                                return "/delete/"+entry_nr
                else:
                        return "/add/"
        
#------------------------------------------------------------------------------------------------------
# Execute the code
#------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

	## read the templates from the corresponding html files
	# .....

	vessel_list = []
	vessel_id = 0
	# Checking the arguments
	if len(sys.argv) != 3: # 2 args, the script and the vessel name
		print("Arguments: vessel_ID number_of_vessels")
        else:
                # We need to know the vessel IP
		vessel_id = int(sys.argv[1])
		# We need to write the other vessels IP, based on the knowledge of their number
		for i in range(1, int(sys.argv[2])+1):
			vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation

	# We launch a server
	server = BlackboardServer(('', PORT_NUMBER), BlackboardRequestHandler, vessel_id, vessel_list)
	print("Starting the server on port %d" % PORT_NUMBER)
 
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
		print("Stopping Server")
#------------------------------------------------------------------------------------------------------
