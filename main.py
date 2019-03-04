import Modules
import psycopg2
import subprocess
conn = psycopg2.connect(host="localhost",database="ditto", user="localrole", password="Noderink1")
minsPassed = 0
while(True):
    Modules.Transcribe.runAutoCheck(conn, 18)
    subprocess.call("sleep 60s", shell=True)

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





