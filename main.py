import Modules
import re
import psycopg2
import time

conn = psycopg2.connect(host="localhost",database="ditto", user="localrole", password="Noderink1")

Modules.Transcribe.updateScript(conn)
# conn.close()
Modules.Transcribe.resetScript(conn, 12)
minsPassed = 0
while(True):
    Modules.Transcribe.runAutoCheck(conn, 12)
    time.sleep(60)
    minsPassed += 1
    # run reset script every 8 hours
    if(minsPassed % 480 == 0):
        Modules.Transcribe.resetScript(conn, 12)

# conn.close()


#Modules.Transcribe.parseNohup(conn)

conn.close()
# filename = "tt"
# import subprocess
# url = "http://traffic.libsyn.com/joeroganexp/p1255.mp3"

# proc = subprocess.Popen("wget -c -O ./" + filename + ".mp3 " + url, shell=True)
# if(proc.wait() != 0):
#     print("of erro.s")
# print("hey fuck")





