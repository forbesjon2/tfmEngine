import requests
import re
from bs4 import BeautifulSoup
import json
import psycopg2
from datetime import datetime
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from shutil import copyfileobj
import time
import xml.etree.cElementTree as etree
import ResolveRouter



class Transcribe:
    def runAutoCheck(dbConnection, maxConcurrent):
        """
        runs an automatic check to see if any transcriptions need to be started or are already finished
        and need to be reuploded\n\n
        Needs dbConnection & an integer representing the max concurrent transcriptons that can be ran at a time\n\n
            This is a function that you dont want to parse and upload files from the 'transcripts' folder into.
            because you really dont know which files are in progress or not whatever. ill fix later .
        """
        # checks if any shows are pending.
        fileContent = DatabaseInteract.checkPre(dbConnection)
        if(len(fileContent) > 0 and Tools.numRunningProcesses() < maxConcurrent):
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE transcriptions SET pending = TRUE WHERE id = '" + fileContent[1] + "';")
            dbConnection.commit()
            cursor.close()
            url = fileContent[0]
            indexID = str(fileContent[1])                                      # get the ID instead of the filename
            service = str(fileContent[3])
            # podcastName = fileContent[2]
            Tools.transcribeAll(service, url, indexID)                            # download the mp3 will print when done



    def updateScript(dbconnection):
        """
        scans all rss feeds for new
        """
        cursor = dbconnection.cursor()
        cursor.execute("select rss, name, source from podcasts;")
        rssArray = cursor.fetchall()
        for rss in rssArray:
            url = str(rss[0])
            name = str(rss[1])
            source = str(rss[2])
            rssArray = DatabaseInteract.rssCheck(name, source, url)
            for item in rssArray:
                if(DatabaseInteract.checkIfExists(dbconnection, item[0]) == False):
                    DatabaseInteract.insertClip(dbconnection, item[2], name, item[3], item[1], item[0])


    def resetScript(dbConnection, maxConcurrent):
        """
        Waits for the running transcription processes to end (2 min intervals). \n
            Then deletes everything in the 'podcasts' folder, parses all transcripts, and updates the 
            databases 
        """
        while (Tools.numRunningProcesses() != 0):                       # wait for the transcriptions to end. Pings every 2 mins
            time.sleep(120)
        emptyPodcastFolder = Tools.cleanupFolder("podcasts")
        DatabaseInteract.refreshDatabase(dbConnection)

    def parseUpload(dbconnection, fileName):
        """
        Requires dbconnection and the filename (location) of the file being parsed
        """
        nhContent = ParseText.nohupTranscriptionContent(fileName)
        count = 0
        while count < len(nhContent[0]):
            try:
                rtf = nhContent[0][count]
                transcription = nhContent[1][count].replace("'", "''").replace("_", "")
                dbID = nhContent[2][count]
                duration = nhContent[3][count]
                DatabaseInteract.insertTranscription(dbconnection, rtf, transcription, duration, dbID)
                count += 1
            except:
                print("couldnt upload one at index " + count)





class ParseText:
    """
    This class handles parsing of two entities: 
        \n\tText files containing one instance of a transcribed podcast or...
        \n\tnohup files containing multiple instances of a transcribed podcast
    """
    def nohupTranscriptionContent(filePath):
        """
        This parses the content of nohup. The size of nohup is basically unlimited but 
        each line has to be under 300000 characters(?). This then returns the following...\n\n
        index 0 -- a list of all the occurences of realTimeFactor\n
        index 1 -- a list of all the occurences of transcriptions\n
        index 2 -- a list of all the occurences of the transcription ID\n
        index 3 -- a list of all the occurences of the total transcription time.\n\n
        \n\n
        \-\---Example usage----\n
        parsedContent = nohupTranscriptionContent("ok.txt")
        for i in range(len(parsedContent[0])):
            print(parsedContent[0][i])          # realtimefactor
            print(parsedContent[1][i])          # transcription
            print(parsedContent[2][i])          # transcription ID
            print(parsedContent[3][i])          # transcription time
        """
        try:
            continu = True
            fileContent = ""
            f = open(filePath, 'r')
            while (continu):
                temp = f.readline(900000)
                if(len(temp) == 0):
                    continu = False
                else:
                    fileContent += temp
            results = []
            realTimeFactor = re.findall(r'Timing stats: real-time factor for offline decoding was (.*?) = ', fileContent)
            results.append(realTimeFactor)
            transcription = re.findall(r'utterance-id(.*?) (.*?)\n', fileContent)
            transcriptionList = []
            transcriptionIDList = []
            for item in transcription:
                if(len(item[1]) > 1000):
                    transcriptionIDList.append(item[0])
                    transcriptionList.append(item[1])
            results.append(transcriptionList)
            results.append(transcriptionIDList)
            transcriptionTime = re.findall(r'seconds  / (.*?) seconds\.', fileContent)
            results.append(transcriptionTime)
            return results
        except Exception as e:
            Tools.writeException("nohupTranscriptionContent", e)
        return False


    def fileTranscriptionContent(filePath):
        """
        This parses the content of the transcription file. The size of the file can basically be unlimited
        but each line has to be under 300000 characters(?). This then returns the following...\n\n
        index 0 -- url\n
        index 1 -- realTimeFactor\n
        index 2 -- transcription\n
        """
        try:
            continu = True
            f = open(filePath, 'r')
            fileContent = ""
            while (continu):
                temp = f.readline(300000)
                if(len(temp) == 0):
                    continu = False
                else:
                    fileContent += temp
            results = []
            f.close()
            url = re.findall(r'URL:(.*?)\n', fileContent)
            results.append(url)
            realTimeFactor = re.findall(r'Timing stats: real-time factor for offline decoding was (.*?) = ', fileContent)
            results.append(realTimeFactor)
            transcription = re.findall(r'utterance-id1 (.*?)\n', fileContent)
            for item in transcription:
                if(len(item) > 500):
                    results.append(item.replace("'", "''"))
            if((len(results[0]) > 0) and (len(results[1]) > 0) and (len(results[2]) > 0)):
                return results
            else:
                Tools.writeException("fileTranscriptionContent", "ERROR attempted to parse " + filePath + " but got " + str(results))
                return False
        except Exception as e:
                Tools.writeException("fileTranscriptionContent", e)
        

        



class Tools:
    """
    Random functions 
    """

    def cleanupFolder(folderName):
        """
        deletes all contents of the specified folder (but not the folder itself).\n
        returns true if successful. False if an error was thrown or the number of running
        processes is not = 0
        """
        try:
            if(Tools.numRunningProcesses() == 0):
                process = subprocess.call('rm -r ./' + folderName + '/*', shell=True)
                return True
            else:
                return False
        except Exception as e:
            Tools.writeException("cleanupFolder", e)
        return False


    def numRunningProcesses():
        """
        gets the number of runnning transcription processes
        """
        try:
            proc = subprocess.run("ps -Af|grep -i \"online2-wav-nnet3-latgen-faster\"", stdout=subprocess.PIPE, shell=True)
            return (len(str(proc.stdout).split("\\n")) - 3)
        except Exception as e:
		        Tools.writeException("numRunningProcesses", e)
        return -1

    def writeException(className, exceptionString):
        """
        Writes Exception given the string format of the class name and the 'e' in any
        Exception as e premise
        """
        errorFile = open("error.log", 'a')
        errorFile.write("ERROR occured in " + className + " at " + str(datetime.now()) + " with the following message\n" + str(exceptionString) + "\n\n")
        errorFile.close()

    def getFirstFile(folderName):
        """
        Returns with the filename of the first file in the given directory. Just provide the directory's name 
        with no leading './'
        """
        listFiles = subprocess.run("ls ./" + folderName, shell=True, stdout=subprocess.PIPE)
        fileName = re.search(r"b'(.*?)\\n", str(listFiles.stdout))[1]
        if(len(fileName) > 0):
            return fileName
        else:
            return False
    def transcribeAll(service, url, fileName):
        """
        Does everything you need to transcribe a podcast given the filename\n
        Download podcast, wait 40 seconds, change podcast to .wav, wait 10 seconds, 
        remove the .mp3 file, run the transcription
        """
        if(service == "omny.fm"):
            url = url.replace(".mp3","") + ".mp3"
        subprocess.Popen("wget -c -O ./podcasts/" + fileName + ".mp3 " + url + " && sleep 40 && ffmpeg -i ./podcasts/"
            + fileName + ".mp3 -acodec pcm_s16le -ac 1 -ar 8000 ./podcasts/" + fileName + ".wav && sleep 10 && rm ./podcasts/" 
            + fileName + ".mp3 && nohup ./online2-wav-nnet3-latgen-faster --online=false --do-endpointing=false "
            + "--frame-subsampling-factor=3 --config=online.conf --max-mem=2000000000 --max-active=7000 --beam=15.0 --lattice-beam=6.0 "
            + "--acoustic-scale=1.0 --word-symbol-table=words.txt final.mdl HCLG.fst 'ark:echo utterance-id" + fileName 
            + " utterance-id"  + fileName + "|' 'scp:echo utterance-id" + fileName + " ./podcasts/" + fileName + ".wav|' 'ark:/dev/null' &", shell=True)





class DatabaseInteract:
    """
    This is where the database is updated. Refer to the example clips/header for format information.\n\n
    Seeding the database would include the usage of 'insertHeader' then 'insertClips'. Pretty much every 
    function in here will require a dbConnection argument
    """
    def uploadPodcast(dbConnection, homepage, name, description, category, source, imageurl, web, twitter, facebook, rss):
        """
        HomePage --> the homepage of the podcast (NOT NULL)\n
        Name --> The name of the podcast (NOT NULL)\n
        Description --> a short description of the podcast\n
        Category --> The category of the podcast\n
        Source --> The service of which the podcast is being accessed through\n
        ImageURI --> Podcast cover art\n
        Web --> The website of the podcaster\n
        Twitter --> The twitter account of the podcaster\n
        Facebook --> the facebook account of the podcaster\n
        LastUpdated --> the date that this was last updated.\n
        RSS --> The URL of the podcasts RSS feed\n
            If you dont have values for a certain field just pass it in as an empty string
        """
        try:
            cursor = dbConnection.cursor()
            name = name.replace("'", "''")
            description = description.replace("'", "''")
            cursor.execute("""INSERT INTO podcasts(homepage, name, description, category, source, imageuri, web, twitter, Facebook, rss) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""", (homepage, name, description, category, source, imageurl, web, twitter, facebook, rss))
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
		        Tools.writeException("insertHeader", "e")
        return False


    def insertClip(dbConnection, audiourl, podcastName, description, parsedDate, title):
        """
        audiourl --> url of the transcriptions mp3 is stored here (NOT NULL)\n
        PodcastName --> THe name of the show (references podcast(name))\n
        Description --> The provided summary of that days podcast\n
        Date --> The date that podcast aired (parsed to mm-dd-yyyy\n
        Title --> The title of that specific podcast\n
        Duration --> the running time of that podcast (use strptime to parse, need mm-dd-yyyy\n
        pending --> right now will be false because were not transcribing\n
        (dateTranscribed) --> date of transcription (updated later)\n
        """
        try:
            cursor = dbConnection.cursor()
            title = title.replace("'", "''")
            cursor.execute("INSERT INTO transcriptions(audiourl, realtimefactor, podcastname, transcription, description, date, title, pending, datetranscribed) VALUES('" + audiourl + "', NULL, '" + podcastName + "', NULL, '" + description + "', '" + parsedDate + "', '" + title + "', FALSE, NULL);")
            dbConnection.commit()
            cursor.close()
            return True
        except:
            return False
        return False
    

    def insertTranscription(dbConnection, realtimefactor, transcription, duration, dbID):
        """
        This basically uploads the arguents to the database, returning false and throwing an 
        error if unsuccesful (or true otherwise)\n
        """
        try:
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE transcriptions SET realtimefactor = '" + realtimefactor + "', transcription = '" + transcription + "', datetranscribed = now(), duration = '" + duration + "' WHERE id = '" + dbID + "';")
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            Tools.writeException("uploadTranscriptionData", e)
        return False



    def checkPre(dbConnection):
        """
        checks the database for empty transcription entries, returns a list with \n\n
        index 0 -- audiourl\n
        index 1 -- id\n
        index 2 -- podcast name\n
        index 3 -- service of podcast
        """
        cursor = dbConnection.cursor()
        cursor.execute("SELECT audiourl, T.id, podcastName, source FROM transcriptions AS T JOIN podcasts as P ON P.name = T.podcastname WHERE COALESCE(T.transcription, '') = '' AND pending = FALSE LIMIT 1;")
        entry = cursor.fetchone()
        cursor.close()
        return entry


    def refreshDatabase(dbConnection):
        """
        This is to be used when both the podcasts folder and transcripts folder are empty.\n
        For every entry in the database that has an empty transcript and a pending flag set to true, change
        the pending flag to false.
            Honestly this is used to deal with a weird bug and should be run every now and then
        """
        try:
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE transcriptions SET pending = FALSE WHERE COALESCE(transcription, '') = '';")
            dbConnection.commit()
            cursor.close()
        except Exception as e:
            Tools.writeException("refreshDatabase", e)

    def checkIfExists(dbconnection, title):
        """
        given title, if the podcast is in the database already return true. False if
        the podcast does not exist in the database
        """
        cursor = dbconnection.cursor()
        output = ""
        title = title.replace("'", "''")
        try:
            cursor.execute("SELECT * FROM transcriptions WHERE title = '" + title + "';")
            dbconnection.commit()
            output = cursor.fetchone()
            cursor.close()
            if(output is None):
                return False
            else:
                return True
        except:
            dbconnection.rollback()
            cursor.execute("SELECT * FROM transcriptions WHERE title = '" + title + "';")
            dbconnection.commit()
            output = cursor.fetchone()
            cursor.close()
            if(output is None):
                return False
            else:
                return True

    def podcastInitRSS(conn, url):
        """
        Gets the following podcast details: 
        name, homepage, description, category, source, web, twitter, facebook, rss \n
            If all match it uploads it to the database
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
                DatabaseInteract.uploadPodcast(conn, homepage, name, description, category, "", image, "", "", "", url)
        except Exception as e:
            Tools.writeException("podcastInitRSS", e + ".\n issue with url " + url)




    def rssCheck(podcastName, source, url):
        """

        """
        try:
            headers = {'Accept':'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8' ,'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'}
            req = requests.get(url, headers=headers)
            root = etree.fromstring(req.text)
            rssArray = []
            for element in root[0].iter('item'):
                title = element.find("title").text.replace("''", "'")
                description = element.find("description").text.replace("<strong>", "").replace("</strong>", "").replace("&amp;", "and").replace("'","''")
                date = element.find("pubDate").text
                date = date.split(" ")
                date = datetime.strptime(date[1] + date[2] + date[3], "%d%b%Y")
                dateString = str(date.month) + "-" + str(date.day) + "-" + str(date.year)
                url = ResolveRouter.urlRouter(podcastName, source, element)
                if(len(title) > 0 and len(description) > 0 and len(dateString) > 0 and len(url) > 0):
                    rssArray.append([title, dateString, url, description])
                else:
                    print("error in XMLDetailsDebug parsing issue")
            return rssArray
        except Exception as e:
            Tools.writeException("getXMLDetailsDebug", e + " with url " + url + " and podcastName " + podcastName)
