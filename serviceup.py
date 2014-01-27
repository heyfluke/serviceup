#!/usr/bin/env python

import os, time, socket, sys, time
import logging
import ConfigParser
import requests
import ping
import smtplib
from configobj import ConfigObj
from urlparse import urlparse
from daemon import Daemon
from webserver import HttpServerInBackground
from BaseHTTPServer import BaseHTTPRequestHandler

"""
Perform setup of variables used in all tasks
"""
logs = os.getcwd()
hostname = socket.gethostname()
log_file = logs + '/serviceup.log'
config_ini = '%s/config.ini' % os.getcwd()
notify_from = 'notify@%s' % hostname
frequency = 5

# Setup logging
logging.basicConfig(filename=log_file, format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%m/%d/%Y %H:%M:%S %z', level=logging.DEBUG)

class WebLogHandler(BaseHTTPRequestHandler):
  daemon = None
  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    message = '<p>monitoring services:\n'
    message += '<table width=90% cellpadding=0 cellspacing=1 border=0 bgcolor=#99cc66>'
    message += '<tr bgcolor=#FFFFFF><td>Service</td><td>Last Check</td><td>Status</td></tr>'
    for k in daemon.services.keys():
      message += '<tr bgcolor=#FFFFFF><td>%s</td><td>%s</td><td>%s</td></tr>' % (k, time.strftime('%m/%d/%Y %H:%M:%S %z', daemon.services[k]['lastcheck']), daemon.services[k]['status'])
    message += '</table>'
    self.wfile.write(message)
    self.wfile.write('\n')
    return

class serviceUp(Daemon):

  services = {}

  def run(self):
    self.setup()
    background_server = None
    if self.config.has_key('webserver_port'):
      logging.info('start web server to serve the status info. listening on port %s' % (int(self.config['webserver_port'])))
      WebLogHandler.daemon = self
      background_server = HttpServerInBackground('0.0.0.0', int(self.config['webserver_port']), webhandler=WebLogHandler).start()
    while True:
      self.delegateTests()
      # Flush stdout so the buffer will write to the log.
      sys.stdout.flush()

      # Sleep until next check.
      time.sleep((frequency * 60))
    if background_server:
      background_server.shutdown()
    logging.info('daemon stopped')

  def setup(self):
    self.parseConfig()
    self.supportedProtocols()

  def parseConfig(self):
    self.config = ConfigObj(config_ini)

  def supportedProtocols(self):
    """
    Need to add other protocols.
    Planned: ping, mysql, solr, APNS
    """
    self.protocols = {'http', 'https'}

  def delegateTests(self):
    for host in self.config:
      for x in self.config[host]:
        #print '>>>>> x:', x
        if x in self.protocols:
          result = self.doTest(x, self.config[host][x])
          if (result):
            logging.info('%s %s test passed', host, x)
          else:
            logging.info('%s %s test failed', host, x)
            self.notify(host, x)
        if x[:7] == 'plugin_':
          result = self.doTestWithPlugin(x[7:], self.config[host][x])
          if (result):
            logging.info('%s %s test passed', host, x)
          else:
            logging.info('%s %s test failed', host, x)
            self.notify(host, x)

  def doTestWithPlugin(self, pluginname, *args):
    #print '>>>> doTestWithPlugin args[0]', args[0]
    service_key = 'plugin_'+pluginname
    if not self.services.has_key(service_key):
      self.services[service_key] = {'lastcheck':time.localtime(), 'status':'UNKNOWN'}

    try:
      pluginmodule = __import__('plugins.%s' % (pluginname,))
      plugin = eval('pluginmodule.%s' % (pluginname,))
      logging.info('running test using plugin %s' % (pluginname,))
      ret = plugin.plugin_entry(**args[0])
      self.services[service_key]['status'] = ret and 'OK' or 'FAIL'
      return ret
    except Exception as e:
      logging.warning(e)
      self.services[service_key]['status'] = 'FAIL'
      return False

  def doTest(self, protocol, *args):
    return getattr(self, 'protocol_'+protocol, self.defaultTest)(*args)

  def defaultTest(self, *args):
    logging.warning("Protocol not supported")

  def protocol_http(self, *args):
    client = args[0]

    service_key = 'http_'+client['url']
    if not self.services.has_key(service_key):
      self.services[service_key] = {'lastcheck':time.localtime(), 'status':'UNKNOWN'}

    logging.info('running http on %s', client['url'])
    try:
      r = requests.get('http://' + client['url'])
      if (r.text):
        if (client['content']):
          pos = r.text.find(client['content'])
          if (pos == -1):
            self.services[service_key]['status'] = 'FAIL'
            return False

        self.services[service_key]['status'] = 'OK'
        return True;
    except Exception as e:
      logging.warning(e)

    self.services[service_key]['status'] = 'FAIL'
    return False

  def protocol_https(self, *args):
    client = args[0]

    service_key = 'https_'+client['url']
    if not self.services.has_key(service_key):
      self.services[service_key] = {'lastcheck':time.localtime(), 'status':'UNKNOWN'}

    logging.info('running https on %s', client['url'])
    try:
      r = requests.get('https://' + client['url'])
      if (r.text):
        if (client['content']):
          pos = r.text.find(client['content'])
          if (pos == -1):
            self.services[service_key]['status'] = 'FAIL'
            return False

        self.services[service_key]['status'] = 'OK'
        return True;
    except Exception as e:
      logging.warning(e)

    self.services[service_key]['status'] = 'FAIL'
    return False

  def notify(self, *args):
    logging.info('emailing %s', self.config['email'])
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s %s is down!\r\n\r\n"
       % (notify_from, self.config['email'], args[0], args[1]))
    msg = msg + "%s %s failed" % (args[0], args[1])
    server = smtplib.SMTP('localhost')
    server.sendmail(notify_from, self.config['email'], msg)
    server.quit()

  def man(self):
    print """
Usage: %s [start|stop|restart|help]
Monitor external services over http(s) and/or ssh
by Jordan Starcher

The log generated by this daemon is %s
""" % (sys.argv[0], log_file)


if __name__ == "__main__":
  daemon = serviceUp('/tmp/serviceup.pid', stdout=sys.stdout, stderr=sys.stderr)
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    elif 'help' == sys.argv[1]:
      daemon.man()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    daemon.man()
    sys.exit(2)
