import psycopg2
from Modules import Omny, DatabaseInteract, Transcribe, Tools, ParseText
import time
import re


def seedFromFiles():
    clipContent = Omny.getFile("./seeds/exampleClips.json")
    headerContent = Omny.getFile("./seeds/exampleHeader.json")
    clipArray = Omny.parseInit(clipContent, "Clips")
    DatabaseInteract.insertHeader(conn, headerContent)
    DatabaseInteract.insertClips(conn, clipArray)



conn = psycopg2.connect(host="localhost",database="ditto", user="localrole", password="Noderink1")

Transcribe.resetScript(conn, 12)
minsPassed = 0
while(True):
    Transcribe.runAutoCheck(conn, 12)
    time.sleep(60)
    minsPassed += 1
    # run reset script every 8 hours
    if(minsPassed % 480 == 0):
        Transcribe.resetScript(conn, 12)
        
conn.close()


