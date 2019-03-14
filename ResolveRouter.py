import psycopg2
import sys 
import Modules
import subprocess
import Modules
import requests
import xml.etree.cElementTree as etree
import re


# The functions in this class are functions that require specific set of operations for a
# certain action and all require 'podcastname' as the first argument. This must be updated 
# every time podcast is added that screws something up. Usually its the URL giving us the issue
# so thats the only thing that needs to be routed at the moment


def urlRouter(podcastName, source, element):
    if(podcastName == "The Joe Rogan Experience"):
        episodeID = re.findall(r'#(.*?)\.', element.find("description").text)
        return "http://traffic.libsyn.com/joeroganexp/p" + str(episodeID[0]) + ".mp3"

    if(source == "omny.fm"):
        return element.find("link").text + ".mp3"
        
    return element.find("enclosure").get("url")