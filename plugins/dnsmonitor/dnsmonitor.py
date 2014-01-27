#!/usr/bin/env python

try:
    import dns.resolver, dns.zone
    from dns.exception import DNSException
    from dns.rdataclass import *
    from dns.rdatatype import *
except ImportError:
    print "Please install dnspython:"
    print "$ sudo pip install dnspython"
    sys.exit(1)

def checkdns(**kwds):
    #print 'check dns hostname %s, nameserver %s' % (kwds['hostname'], kwds['nameserver'])
    try:
        import dns.resolver
        my_resolver = dns.resolver.Resolver()
        my_resolver.nameservers = [kwds['nameserver']]
        answer = my_resolver.query(kwds['hostname'])
        return True
    except Exception, e:
        return False

if __name__ == '__main__':
    d = {'hostname':'www.github.com', 'nameserver':'8.8.8.8'}
    ret = checkdns(**d)
    print 'checkdns ret %d' % (ret,)