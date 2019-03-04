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
    Parses the NPR feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763', 'Host': 'www.npr.org'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        rssArray = []
        for element in root[0].iter('item'):
            title = element.find("title").text.replace("''", "'")
            description = element.find("description").text.replace("'", "''")
            date = element.find("pubDate").text
            date = date.split(" ")
            date = datetime.strptime(date[1] + date[2] + date[3], "%d%b%Y")
            dateString = str(date.month) + "-" + str(date.day) + "-" + str(date.year)
            url = element.find("enclosure").get("url")
            rssArray.append([title, dateString, url, description])
        return rssArray
    except Exception as e:
        Modules.Tools.writeException("NPR getXML", e)


def downloadMp3(url):
    proc = subprocess.Popen("wget -c -O ./podcasts/" + filename + ".mp3 " + url, shell=True)
    if(proc.wait() != 0):
        Modules.Tools.writeException("NPR download", "proc.wait() returned an exception")
    # wait 2 mins
    time.sleep(120)
    return
