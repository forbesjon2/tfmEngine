import psycopg2
import sys 
sys.path.insert(0, "./Providers")
import JoeRogan, NPR, Omny


# The functions in this class are functions that require specific set of operations for a
# certain action and all require 'podcastname' as the first argument. This must be updated 
# every time podcast is added. (the number of podcast entries in the database must equal
# the number of cases in the respective switch case in this class)


# ---------------------------IMPORTANT----------------------------
# (sql statements for manual updates go here)

    
def uploadContent(podcastName, source ):
    """
    routes get content
    """
    if(podcastName == "Mark Levin Audio Rewind"):
        return Omny.getContent(url, withHeader)
    # joe rogan podcast
    if(podcastName == ""):
        pass

def parseXML(podcastName, source, url):
    """
    parses the XML from the podcasts RSS feed and is to be used as the main
    means of retrieving new content
    Unfortunately, not every podcast has the same format for XML so all thats needed is the rss feed url\n
    Returns an array of the following values\n
    index 0 -- Title\n
    index 1 -- Date of podcast (mm-dd-yyyy)\n
    index 2 -- audio url (mp3)\n 
    index 3 -- description\n
    """
    if(podcastName == "The Joe Rogan Experience"):
        return JoeRogan.getXML(url)
    if(source == "NPR"):
        return NPR.getXML(url)
    if(source == "omny.fm"):
        return Omny.getXML(url)
