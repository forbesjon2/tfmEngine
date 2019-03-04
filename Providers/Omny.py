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
    Parses the Omny feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8', 'Host': 'www.omnycontent.com','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        rssArray = []
        for element in root.iter('item'):
            title = element.find("title").text.replace("''", "'")
            description = element.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary").text.replace("'", "''")
            date = element.find("pubDate").text
            date = date.split(" ")
            date = datetime.strptime(date[1] + date[2] + date[3], "%d%b%Y")
            dateString = str(date.month) + "-" + str(date.day) + "-" + str(date.year)
            actualUrl = element.find("link").text + ".mp3"
            rssArray.append([title, dateString, actualUrl, description])
        return rssArray
    except Exception as e:
        Modules.Tools.writeException("omny getXML", e)