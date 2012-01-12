# Controller for subi webservice
#
# adapted from 
#   Jon Berg , turtlemeat.com
#   http://fragments.turtlemeat.com/pythonwebserver.php
#
# by 
#   Ben Haley - Dec 2011
#   <benjamin.haley@gmail.com> 

webdir = 'web'
home_url = 'http://localhost/subi'

import string,cgi,time
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from db import subi_db
import json

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print("Requested " + self.path)
        req = urlparse(self.path)
        try:
            # serve static content as is
            if req.path in ["/css/bootstrap/bootstrap.css", "/favicon.ico"]:
                fpath = req.path

            # Handle erroneous requests
            elif req.path.endswith("/404"):
                fpath = "/404.html"

            # return the front page
            elif req.path == "/subi":
                fpath = "/subi.html"

            # return search page
            elif req.path == "/subi/search":
                fpath = "/search.html"

            # return data entry page
            elif req.path == "/subi/update":
                fpath = "/update.html"

            # return data entry page
            elif req.path == "/subi/organize":
                fpath = "/organize.html"

            # handle data requests
            elif req.path == "/subi/ajax":
                self.do_AJAX()
                return

            elif req.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("hey, today is the" + str(time.localtime()[7]))
                self.wfile.write(" day in the year " + str(time.localtime()[0]))
                return
            else:
                self.send_response(301)
                self.send_header('Location', '404')
                self.end_headers()
                return

            f = open(webdir + fpath)
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

        except IOError:
            self.send_error( 404,
                             'File Not Found: %s.  Please visit %s ' 
                             % (self.path, home_url)
                           )

    def do_AJAX(self):
        """
            This is outside the specification.
            It will handle any ajax query with a json response.
            Errors will be noted in json.
        """
        req = urlparse(self.path)
        q = parse_qs(req.query)
        print("Query contains: " + str(q))

        db = subi_db.subi_db_class()

        # Determine command
        if 'command' not in q:
            response = {'error': 'No command in query, ' + self.path}
            command = "NO COMMAND SENT"
        else:
            command = q['command'][0]
            print("command: " + command)

        # Execute command
        try:
            if command == "NO COMMAND SENT":
                pass

            elif command == "create_col":
		if 'col_group' not in q:
		     q['col_group'] = [None]
                db.create_col(
				 q['col_name'][0],
				 q['col_type'][0],
				 q['col_desc'][0],
				 q['col_group'][0]
			      )
		response = {'ok': True}
            
            elif command == "update_col":
		if 'col_group' not in q:
		     q['col_group'] = [None]
                db.create_col(
				 q['old_col_name'][0],
				 q['new_col_name'][0],
				 q['col_type'][0],
				 q['col_desc'][0],
				 q['col_group'][0]
			      )
		response = {'ok': True}

            elif command == "delete_col":
                db.delete_col(q['col_name'][0])
                response = {'ok': True}

            elif command == "insert_new_animal":
                db.insert_new_animal(q['animal_id'][0])
                response = {'ok': True}

            elif command == "delete_animal":
                db.delete_animal(q['animal_id'][0])
                response = {'ok': True}

            elif command == "sql":
                response = {"cool duche bag"}
                
            else:
                response = {'error': 'Unrecognized command, ' + command}
       
        except Exception as e: 
	     raise 
             #response = {'error': e[0]}

        print db.run_sql_query("SELECT * FROM animals")
        print db.run_sql_query("SELECT * FROM col_definitions")

        # Send back some json
        self.wfile.write(response)
        return

        # db.create_col(col_name, col_type, col_desc, col_group)
     

    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)
            
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);
            
        except :
            pass

def main():
    try:
        server = HTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

