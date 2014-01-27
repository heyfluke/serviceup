#!/usr/bin/env python

def plugin_entry(**kwds):
    from dnsmonitor import checkdns
    return checkdns(**kwds)