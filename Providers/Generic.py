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
import ResolveRouter
def getXML(podcastName, source, url):
    """
    Parses the NPR feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
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
            url = ResolveRouter.urlRouter(podcastName, source, element)
            rssArray.append([title, dateString, url, description])
        return rssArray
    except Exception as e:
        Modules.Tools.writeException("NPR getXML", e)




def getXMLDetails(url):
    """
    Parses the NPR feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
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
        pass


def getXMLDetailsDebug(podcastName, source, url):
    """
    Parses the NPR feed. Returns with a 2d array with the following information\n
    index 0 -- Title
    index 1 -- Date of podcast (mm-dd-yyyy)
    index 2 -- audio url (mp3)
    index 3 -- description
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        rssArray = []
        for element in root[0].iter('item'):
            # print("title " + element.find("title").text.replace("''", "'"))
            description = element.find("description").text.replace("<strong>", "").replace("</strong>", "").replace("&amp;", "and").replace("'","''")
            # print("description " + description)
            # print(len(description))
            date = element.find("pubDate").text
            date = date.split(" ")
            date = datetime.strptime(date[1] + date[2] + date[3], "%d%b%Y")
            dateString = str(date.month) + "-" + str(date.day) + "-" + str(date.year)
            # print("date string " + dateString)
            url = ResolveRouter.urlRouter(podcastName, source, element)
            print("url " + url)
    except Exception as e:
        print("error in debug " + e )

























def getPodcastDetails(url):
    """
    Gets the following podcast details
    name, description, category, source, web, twitter, facebook, rss
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        resArray = []
        homepage = root[0].find("link").text
        name = root[0].find("title").text
        description = ""
        try:
            description = root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary").text
        except:
            pass
        try:
            description = root[0].find("description").text
        except: 
            pass
        category = root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}category").attrib["text"]
        image = root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image").attrib["href"]
        if(len(name) > 0 and len(description) > 0 and len(category) > 0 and len(image) > 0 and len(homepage) > 0):
            print("all pass.. got ")
            print(name)
            print(homepage)
            print(description)
            print(category)
            print(image)
    except Exception as e:
        pass
        # Modules.Tools.writeException("NPR getXML", e)




def getPodcastDetailsDebug(url):
    """
    Gets the following podcast details
    name, description, category, source, web, twitter, facebook, rss
    """
    try:
        headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
        req = requests.get(url, headers=headers)
        root = etree.fromstring(req.text)
        resArray = []
        print(root[0].find("link").text)
        print(root[0].find("title").text)
        print(root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary").text)
        print(root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}category").attrib["text"])
        print(root[0].find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image").attrib["href"])
    except Exception as e:
        pass
        # Modules.Tools.writeException("NPR getXML", e)

