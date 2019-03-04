import subprocess
import sys
sys.path.insert(0, "../")
import Modules
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import xml.etree.cElementTree as etree
import re
from datetime import datetime
import time

def getXML(url):
    """
    Parses the joe rogan feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.8, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763', 'Host': 'podcasts.joerogan.net'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        rssList = []
        for element in root[0].iter('item'):
            title = element.find("title").text
            date = element.find("pubDate").text
            descPre = element.find("description").text
            episodeID = re.findall(r'#(.*?)\.', descPre)
            date = date.split(" ")
            date = datetime.strptime(date[1] + date[2] + date[3], "%d%b%Y")
            dateString = str(date.month) + "-" + str(date.day) + "-" + str(date.year)
            url = "http://traffic.libsyn.com/joeroganexp/p" + episodeID[0] + ".mp3"
            description = re.findall(r'\.(.*?)<p>', descPre)
            description = description[0].replace("<strong>", "").replace("</strong>", "").replace("&amp;", "and").replace("'","''")
            rssList.append([title, dateString, url, description])
        return rssList
        return rssList
    except Exception as e:
        Modules.Tools.writeException("JoeRogan getXML", e)


def downloadMp3(url):
    # "http://traffic.libsyn.com/joeroganexp/p1255.mp3"
    proc = subprocess.Popen("wget -c -O ./podcasts/" + filename + ".mp3 " + url, shell=True)
    if(proc.wait() != 0):
        Modules.Tools.writeException("JoeRogan download", "proc.wait() returned an exception")
    time.sleep(150)
    return
    
