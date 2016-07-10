import sys
import os
sys.path.insert(1, os.path.split(sys.path[0])[0])
from cli import CommandLineInterface
import nfc
clf = nfc.ContactlessFrontend('usb')

def connected(tag):
    print tag.ndef.message.pretty()

clf.connect(rdwr={'on-connect': connected})
