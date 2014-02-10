from django.core.management import setup_environ
from sys import path 
path.append("..")
from Fingerprints_django import settings
setup_environ(settings)
from django.core.cache import cache

print cache
key = "test_key"

def store_test(val):
 cache.set(key, val)
 if cache.get(key) is not None:
  cache.delete(key)
  return True
 else:
  return False

from numpy import arange
from pickle import loads, dumps

i = 10
while i <= 1000000:
 as_str = dumps(arange(i))
 # yes = store_test(arange(i))
 yes = store_test(as_str)
 byte_count = len(as_str)*2
 if yes:
        print "stored", byte_count, "bytes successfully"
 else:
        print "failed to store", byte_count, "bytes"
 i *= 10
