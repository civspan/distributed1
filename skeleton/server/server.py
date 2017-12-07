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
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
import time

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
		# our own ID (IP is 10.1.0.ID)
		self.vessel_id = vessel_id
		# The list of other vessels
		self.vessels = vessel_list
                # Logical clock of this vessel
                self.clock = 0
                # Todo-list
                self.todo = {}
                self.start_time = 0
                self.end_time = 0
                
#------------------------------------------------------------------------------------------------------                
	# We add a value received to the store
	def add_value_to_store(self, label, value):
		# We add the value to the store
                #print("Added value %s with label %d" % (value,self.clock))
                self.store[label] = (label,value)
                if self.start_time == 0:
                        self.start_time = time.time()
                self.end_time = time.time()
                print 'Elapsed time: ',self.end_time - self.start_time
                print 'start time: %s end time: %s' %(str(self.start_time)[8:], str(self.end_time)[8:])

#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
	def modify_value_in_store(self,label, msg_id,value):
		# we modify a value in the store if it exists
                try:
                        print("Modified stored value at index %s from %s to %s" % (label,self.store[label],value))
                        self.store[label]= (msg_id,value)
                except KeyError:
                        print("Key %d not present when modifying in vessel %d" % (label,self.vessel_id))
                if self.start_time == 0:
                        self.start_time = time.time()
                self.end_time = time.time()
                print 'Elapsed time: ',self.end_time - self.start_time
                print 'start time: %s end time: %s' %(str(self.start_time)[7:], str(self.end_time)[7:])
#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,label):
		# we delete a value in the store if it exists
		try:
                        print("Deleted value stored at key [%s] from store" % (label))
                        del self.store[label]
                except Exception as e:
                        print("Error while deleting key %s from vessel %d" % (label,self.vessel_id))
                        print(e)
                if self.start_time == 0:
                        self.start_time = time.time()
                self.end_time = time.time()
                print 'Elapsed time: ',self.end_time - self.start_time
                print 'start time: %s end time: %s' %(str(self.start_time)[8:], str(self.end_time)[8:])

#------------------------------------------------------------------------------------------------------
        # Getter for the stored entries
        def get_store(self):
                return self.store

#------------------------------------------------------------------------------------------------------
        #Getter for current index
        def get_clock(self):
                return self.clock

#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, label, msg_id, value):
		# the Boolean variable we will return
		success = False
		# The variables must be encoded in the URL format, through urllib.urlencode.
                # The variables passed to another vessel depend on the specified path in the function call
                post_content = ""
                if "add" in path:
                        post_content = urlencode({'entry' : value, 'label' : label, 'msg_id' : msg_id}) # value is (msg_id, val)
                elif "status" in path:
                        post_content = urlencode({'label': label, 'requester_id' : msg_id[0], 'replier_id' : msg_id[1], 'answer': value })
                elif "delete" in path:
		        post_content = urlencode({'entry' : value, 'label' : label, 'msg_id' : msg_id, "delete" : 1})
                else:
                        post_content = urlencode({'entry' : value, 'label' : label, 'msg_id' : msg_id, "delete" : 0})

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
# Send a received value to all the other vessels of the system
#------------------------------------------------------------------------------------------------------
	def propagate_value_to_vessels(self, path, label, msg_id, value):
                # We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				# A good practice would be to try again if the request failed
				# Here, we do it only once.
				self.contact_vessel(vessel, path, label,msg_id, value)		
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
                store_array = self.server.store.items()
                
                for item in sorted(sorted(store_array,key=lambda x:eval(x[1][0])[0]),\
                                    key=lambda y:eval(y[1][0])[1],reverse=True) :
                        with open(entry_template) as html_file:
                                label = item[0]
                                tmp = html_file.read()
                                html_entries += tmp % ("entries/"+str(label),str(label),self.server.store[label][1])
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
                path = self.path
                val = post_data['entry'][0]
                        
            
                # The boolean retransmit is used to specify whether this node should propagate the
                # post. We check the path in the header to determine whether it should retransmit or
                # not. After an operation, the path is altered in order to avoid cyclic retransmission.
                retransmit = True
                label = ''
                 # Message is from another vessel
                if "receive" in path:
                        post_data['label'] = post_data['label'][0]
                        post_data['msg_id'] = post_data['msg_id'][0]
                        retransmit = False
                        label = post_data['label']
               
                # Message is an add from this vessels board
                if "board" in path:
                        label = str((self.server.vessel_id,self.server.clock))
                        post_data['label'] = label
                        post_data['msg_id'] = label
                # Message is a del or mod from this vessels board
                elif 'entries' in path:
                        #get index (key) of entry from path and cast to int
                        path = path.replace('%20',' ')
                        result =  re.search('\([\d]+, [\d]+\)', path) 
                        label = result.group()
                        post_data['label'] = label
                        post_data['msg_id'] = str( (self.server.vessel_id, self.server.clock) )
               
                # The operations are added to the path so that all clients can determine the correct
                # action for this POST. The path combined with the POST body is used when determining
                # the action.

                # An entry is stored in post_data as such: {'entry': ['sven']}
                # The path to add a value to index 0 is: /entries/0
                if "status" in path:
                # Check to see if the message is a status request or reply by seeing if the
                # message was created by this vessel
                        label = post_data['label'][0]
                        replier_id = eval(post_data['replier_id'][0])
                        requester_id = eval(post_data['replier_id'][0])
                        if self.server.vessel_id == replier_id:
                                vessel_ip = '10.1.0.' + requester_id
                                vessels = (requester_id,replier_id)
                                answer = post_data['label'] in self.server.store
                                thread = Thread(target=self.server.contact_vessel,args=\
                                                (vessel_ip,label,'status-reply', vessels, answer))
                                # We kill the process if we kill the server
			        thread.daemon = True
			        # We start the thread
			        thread.start()
                        elif label in self.server.todo:
                                answer = eval(post_data['answer'][0])
                                if answer and self.server.todo[label][2] == "mod":
                                       self.server.add_value_to_store(label,self.server.todo[label][1])
                                del self.server.todo[label]
                if "delete" in post_data:
                        print "Deleting..."
                        label_string = str(label)
                        label_string = label_string.replace(' ', '%20')
                        # Delete is 0 -> modify data
                        if post_data['delete'][0] == '0':
                                path = "/receive/modify/"+label_string
                                self.modify(post_data)
                        # Delete is 1 -> delete data
                        else:
                                path = "/receive/delete/"+label_string
                                self.delete(post_data)
                else:
                        path = "/receive/add/"
                        self.add(post_data)
                 # Not a status message - increment clock
                if 'status' not in path and not retransmit:
                        self.increment_clock(post_data)

                for thing in self.server.todo:
                        print thing + ' in todo'
                        
		if retransmit:
			# do_POST send the message only when the function finishes
			# We must then create threads if we want to do some heavy computation
			# 
			# Random content
                        msg_id = (self.server.vessel_id, self.server.clock)
			thread = Thread(target=self.server.propagate_value_to_vessels,args=\
                                        (path,label,msg_id,post_data["entry"][0]))
                        self.increment_clock(post_data)

			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start()
                
#------------------------------------------------------------------------------------------------------
# Handle "delete" message 
#------------------------------------------------------------------------------------------------------
        def delete(self,post_data):
                label = post_data['label']
                if label in self.server.todo:
                        if self.server.todo[label][2] == 'mod':
                                self.server.todo[label][2] = 'del'
                else:
                        print ''+label+' not in todo'
                        if label in self.server.store:
                                self.server.delete_value_in_store(label)
                        else:
                                self.server.todo[label] = ('', '', 'del')
                                vessels = (self.server.vessel_id, eval(post_data['msg_id'])[0])
                                vessel_ip = '10.1.0.%d' % vessels[1]
                                thread = Thread(target=self.server.contact_vessel,args=\
                                                (vessel_ip,label,'status-request', vessels,'request'))
                                # We kill the process if we kill the server
			        thread.daemon = True
			        # We start the thread
			        thread.start()
                                
                                                
#------------------------------------------------------------------------------------------------------
# Handle "modify" message
#------------------------------------------------------------------------------------------------------
        def modify(self,post_data):
                label = post_data['label']
                entry = post_data['entry'][0]
                msg_id = post_data['msg_id']
                if label in self.server.todo:
                        if self.server.todo[label][2] == 'mod':
                                if self.is_newer(msg_id, self.server.todo[label][0]):
                                        self.server.todo[label][1] = entry
                else:
                        if label in self.server.store:
                                if self.is_newer(msg_id, self.server.store[label][0]):
                                        self.server.modify_value_in_store(label,msg_id,entry)
                        else:
                                msg_id = string_to_tuple(msg_id)
                                self.server.todo[label] = (msg_id,entry,'mod')
                                vessels = (self.server.vessel_id, eval(post_data['msg_id'])[0])
                                vessel_ip = '10.1.0.%d' % vessels[1]
                                thread = Thread(target=self.server.contact_vessel,args=\
                                                (vessel_ip,label,'status-request', vessels,'request'))
                                # We kill the process if we kill the server
			        thread.daemon = True
			        # We start the thread
			        thread.start()
                                                
#------------------------------------------------------------------------------------------------------
# Handle "add" message 
#------------------------------------------------------------------------------------------------------
        def add(self,post_data):
                label = post_data['label']
                if label in self.server.todo:
                        if self.server.todo[label][2] == 'mod':
                                self.server.add_to_store(label,self.server.todo[label][1])
                        del self.server.todo[label]
                else:
                        self.server.add_value_to_store(label,post_data['entry'][0]) # kolla detta för rätt värde
                        
              
#------------------------------------------------------------------------------------------------------
# Cast string of tuple to tuple of ints
#------------------------------------------------------------------------------------------------------
        def string_to_tuple(string):
                 return eval(string)


#------------------------------------------------------------------------------------------------------
# Compare two message id's and determine causality 
#------------------------------------------------------------------------------------------------------
        def compare_msg_id(msg_id):
                return eval(msg_id)[1]

#------------------------------------------------------------------------------------------------------
# Compare two message id's and determine causality 
#------------------------------------------------------------------------------------------------------
        def is_newer(self,msg_id1, msg_id2):
                msg_id1 = eval(msg_id1)
                msg_id2 = eval(msg_id2)
                if msg_id1[1] == msg_id2[1]:
                        return msg_id1[0] > msg_id2[0]
                else:
                        return msg_id1[1] > msg_id2[1]
                                                
#------------------------------------------------------------------------------------------------------
# Increment the logical clock based on the maximum of received clock and own clock
#------------------------------------------------------------------------------------------------------
        def increment_clock(self,post_data):
                sender_clock = eval(post_data['msg_id'])[1]
                self.server.clock = max(sender_clock, self.server.clock) + 1 # {entry: [ (0,0),(3,1),'sven']}

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

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
		print("Stopping Server")
#------------------------------------------------------------------------------------------------------
