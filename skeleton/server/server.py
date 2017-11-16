
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
import sys
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
	def __init__(self, server_address, handler, node_id, vessel_list):
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
                self.num_vessels = len(vessel_list)
                # Randomized integer used in leader election
                self.rand_num = randint(0,self.num_vessels*200)
                # Next node in a ring topology for leader election
                self.next_vessel = (vessel_id % self.num_vessels) + 1
                # List of leader election results
                self.election_results = []
                # Set true if this vessel is elected leader
                self.is_leader = False
                # Set id of leader after election
                self.leader_id = -1
                
                # Wait for nodes to initialize, then initiate leader election and add own results to election list
                #sleep(1)                
                target_ip = "10.1.0.%s" % self.next_vessel
                self.contact_vessel(target_ip, "/elect_mode/e/", str(self.vessel_id), str(self.rand_num))
                self.election_results.append( (self.vessel_id, self.rand_num) )

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
        # Getter for the stored entries
        def get_store(self):
                return self.store

#------------------------------------------------------------------------------------------------------
        #Getter for current index
        def get_current_key(self):
                return self.current_key

#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, key, value):                
		# the Boolean variable we will return
		success = False
		# The variables must be encoded in the URL format, through urllib.urlencode.
                # The variables passed to another vessel depend on the specified path in the function call
                post_content = ""
                if "add" in path:
                        post_content = urlencode({key : value})       
                elif "delete" in path:
		        post_content = urlencode({key : value, "delete" : 1})
                elif "modify" in path:
                        post_content = urlencode({key : value, "delete" : 0})
                elif "elect" in path:
                        post_content = urlencode({key : value, "elect_mode" : "e"})
                         
                #print post_content
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
		print("Receiving a GET on path %s" % self.path)
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
                for entry in self.server.get_store():
                        with open(entry_template) as html_file:
                                tmp = html_file.read()
                                html_entries += tmp % ("entries/"+str(entry),entry,self.server.get_store()[entry])
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

                # The boolean retransmit is used to specify whether this node should propagate the
                # post. We check the path in the header to determine whether it should retransmit or
                # not. After an operation, the path is altered in order to avoid cyclic retransmission.
                retransmit = True
                if "receive" in self.path:
                        retransmit = False
                        
                # The operations are added to the path so that all clients can determine the correct
                # action for this POST. The path combined with the POST body is used when determining
                # the action.

                # An entry is stored in post_data as such: {'entry': ['sven']}
                # The path to add a value to index 0 is: /entries/0
                if "delete" in post_data:
                        self.do_delete_or_modify(post_data)
                elif "entry" in post_data:
                        self.do_add(post_data)
                # If message is a leader election message, append to election list
                else:
                        self.do_election(post_data)

		if retransmit and self.server.is_leader:
                        self.do_retransmit(post_data)


#------------------------------------------------------------------------------------------------------

        def do_delete_or_modify(self,post_data):
                #get index (key) of entry from path and cast to int
                key_string =  re.search('[\d]+', self.path).group()
                key = int(key_string)

                # Delete is 0 -> modify data
                if post_data['delete'][0] == '0':
                        self.path = "/receive/modify/"+key_string
                        self.server.modify_value_in_store(key,post_data["entry"][0])
                        # Delete is 1 -> delete data
                else:
                        self.path = "/receive/delete/"+key_string
                        self.server.delete_value_in_store(key)

        def do_add(self,post_data):
                self.path = "/receive/add/"
                self.server.add_value_to_store(post_data["entry"][0])

        def do_election(self,post_data):
                self.path = "/leader_election/"
                print "YEAH"
                #post_key = post_data.keys()[0]
                #self.election_results.append(post_key, post_data[post_key])
                #if len(self.election_results) < self.num_vessels:
                #        contact_vessel("10.1.0.%s" % self.vessel_id, self.path, post_key, post_data[post_key])
                #else:
                #        print "Leader election done"

        def do_retransmit(self,post_data):
		# do_POST send the message only when the function finishes
		# We must then create threads if we want to do some heavy computation
		# 
		# Random content
		thread = Thread(target=self.server.propagate_value_to_vessels,args=\
                                (self.path,"entry",post_data["entry"][0]))
		# We kill the process if we kill the server
		thread.daemon = True
		# We start the thread
		thread.start()
	                
#------------------------------------------------------------------------------------------------------
# Execute the code
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
        sleep(1)
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
		print("Stopping Server")
#------------------------------------------------------------------------------------------------------


# Questions of TA's:
# 1 Do we need "c" message?
# 2 When do we call sleep?
#
