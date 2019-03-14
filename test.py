import Modules
import ResolveRouter
import sys 
sys.path.insert(0, "./Providers")
import Generic
import psycopg2
conn = psycopg2.connect(host="localhost",database="ditto", user="localrole", password="Noderink1")


# To add podcast...
# name, description, category, source, web, twitter, facebook, rss
# name, description, category, source, rss

# resArray = Generic.getXML("https://rss.art19.com/phil-in-the-blanks")
# Generic.getXML("https://rss.art19.com/over-my-dead-body")
# Generic.getPodcastDetails("https://rss.art19.com/over-my-dead-body")
# Generic.getPodcastDetailsOther("http://feeds.soundcloud.com/users/soundcloud:users:174770374/sounds.rss")
# Generic.getPodcastDetails("http://feeds.soundcloud.com/users/soundcloud:users:174770374/sounds.rss")
# Generic.getPodcastDetails("https://rss.simplecast.com/podcasts/4123/rss")
# Generic.getPodcastDetails("https://www.npr.org/rss/podcast.php?id=510334")
# Generic.getPodcastDetails("https://feeds.megaphone.fm/HSW7933892085")
# Generic.getXMLDetailsDebug("https://feeds.megaphone.fm/HSW7933892085")
# Generic.getXMLDetailsDebug("https://www.npr.org/rss/podcast.php?id=510334")
# Generic.getXMLDetailsDebug("https://rss.simplecast.com/podcasts/4123/rss")
# Generic.getXMLDetailsDebug("http://feeds.soundcloud.com/users/soundcloud:users:174770374/sounds.rss")
# Generic.getXMLDetailsDebug("https://rss.art19.com/over-my-dead-body")
# Generic.getXMLDetailsDebug("ss", "omny.fm", "https://www.omnycontent.com/d/playlist/a7b0bd27-d748-4fbe-ab3b-a6fa0049bcf6/392196e7-87cf-4af5-b31b-a89c01057741/2bab9367-8229-4d22-ad4c-a89c01057758/podcast.rss")
# Generic.getXMLDetailsDebug("The Joe Rogan Experience", "x", "http://podcasts.joerogan.net/feed")

Modules.Transcribe.updateScript(conn)
#Modules.DatabaseInteract.podcastInitRSS(conn, "https://rss.art19.com/phil-in-the-blanks")
#Modules.DatabaseInteract.podcastInitRSS(conn, "https://rss.art19.com/over-my-dead-body")
#Modules.DatabaseInteract.podcastInitRSS(conn, "http://feeds.soundcloud.com/users/soundcloud:users:174770374/sounds.rss")
#Modules.DatabaseInteract.podcastInitRSS(conn, "https://rss.simplecast.com/podcasts/4123/rss")
#Modules.DatabaseInteract.podcastInitRSS(conn, "https://feeds.megaphone.fm/HSW7933892085")

conn.close()
