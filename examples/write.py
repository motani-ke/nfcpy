import sys
import os
sys.path.insert(1, os.path.split(sys.path[0])[0])
import nfc
import nfc.ndef
clf = nfc.ContactlessFrontend('usb')

def connected(tag):
    record1 = nfc.ndef.Record("urn:nfc:wkt:T", "publicUserId", "This is sample publicUserId.")
    record2 = nfc.ndef.Record("urn:nfc:wkt:T", "okazu", "Hello World!")
    tag.ndef.message = nfc.ndef.Message(record1, record2)
    print tag.ndef.message.pretty()

clf.connect(rdwr={'on-connect': connected})
