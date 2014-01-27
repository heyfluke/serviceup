from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading, time, sys

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message =  threading.currentThread().getName()
        self.wfile.write(message)
        self.wfile.write('\n')
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class BackgroundThread(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
 
    def run(self):
        global count, mutex
        threadname = threading.currentThread().getName()
        self.server.serve_forever()

class HttpServerInBackground():
    def __init__(self, host='0.0.0.0', port=8000, webhandler=None):
        self.server = ThreadedHTTPServer((host, port), webhandler and webhandler or Handler)
        self.backgroundThread = BackgroundThread(self.server)

    def start(self):
        self.backgroundThread.start()
        return self

    def shutdown(self):
        self.server.shutdown()
        self.backgroundThread.join()

if __name__ == '__main__':
    '''
    server = ThreadedHTTPServer(('localhost', 8000), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    #server.serve_forever()
    backgroundThread = BackgroundThread(server)
    backgroundThread.start()
    '''
    background_server = HttpServerInBackground('0.0.0.0', 8000).start()
    try:
        while True:
            print 'x', 
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print '<Ctrl-C>, shutdown server'
        background_server.shutdown()