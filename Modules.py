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
            url = fileContent[0]
            fileName = str(fileContent[1]).replace(" ", "x").replace("/", "x").replace("\\", "x") 
            fileInit= open("./transcripts/" + fileName + ".txt", "w")
            fileInit.write("URL:" + url + "\nname:" + fileContent[1])
            fileInit.close()
            soup = Omny.getContent(url, False)                          # get the webpage in beautifulsoup format
            description = soup.findAll("meta")[2]["content"]            # parse the description (as soup^)
            DatabaseInteract.updateDescription(dbConnection, description, url) # upload the description
            song = Tools.downloadMp3(url, fileName)                     # download the mp3
            Tools.convertToWav(fileName)                                # convert it to wav and delete the file
            Tools.runTranscription(fileName)                            # runs the transcription and writes results to ./transcripts




    def resetScript(dbConnection, maxConcurrent):
        """
        Waits for the running transcription processes to end (2 min intervals). \n
            Then deletes everything in the 'podcasts' folder, parses all transcripts, and updates the 
            databases 
        """
        while (Tools.numRunningProcesses() != 0):                       # wait for the transcriptions to end
            time.sleep(120)
        emptyPodcastFolder = Tools.cleanupFolder("podcasts")
        emptyTranscriptionFolder = Transcribe.parseUploadTranscripts(dbConnection)
        if(emptyPodcastFolder and emptyTranscriptionFolder):
            DatabaseInteract.refreshDatabase(dbConnection)
        
    def parseUploadTranscripts(dbConnection):
        """
        This runs through the process of...
        Getting the first file in the transcripts folder and parsing it
        Uploading the parsed file to the database
        """
        try:
            fileName = Tools.getFirstFile("transcripts")
            while(len(fileName) > 0):
                parsedContent = ParseText.fileTranscriptionContent("./transcripts/" + fileName)
                if(parsedContent):
                    subprocess.run("rm ./transcripts/" + fileName, shell=True)      # remove the file once we have the content
                    uploadResult = DatabaseInteract.uploadTranscriptionData(dbConnection, parsedContent[0], parsedContent[1], parsedContent[2], parsedContent[3])
                else:
                    Tools.writeException("parseUploadTranscripts", "ERROR getting the parsedContent from file " + fileName)
                    return False
        except Exception as e:
            Tools.writeException("parseUploadTranscripts", e)
        return False
            
    def parseUploadNohup(dbConnection):
        """
        This runs through the process of...
        Reading nohup.out and getting all instances of transcripted files 
        then uploading it to the database and then deleting nohup.out if successful.
        This is meant to be modified with different podcasts. \n\n
            but seriously nohup is a really bad place to store transcripts
        """
        try:
            resultArray = ParseText.nohupTranscriptionContent("nohup.out")
            for index in range(len(resultArray[0])):
                rtf = resultArray[0][index]
                transcription = resultArray[1][index].replace("'", "''")
                name = re.sub(r'[^1234567890x]', "", resultArray[2][index])
                name = name.replace("xxx", "").replace("xx", "").replace("x","/")
                DatabaseInteract.uploadTranscriptionDataModified(dbConnection, name, rtf, transcription)
        except Exception as e:
            Tools.writeException("parseUploadNohup", e)
            





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
        index 0 -- a list of all the occurences of realTimeFactor
        index 1 -- a list of all the occurences of transcriptions
        index 2 -- a list of all the occurences of the transcription name.
        """
        try:
            continu = True
            fileContent = ""
            f = open(filePath, 'r')
            while (continu):
                temp = f.readline(300000)
                if(len(temp) == 0):
                    continu = False
                else:
                    fileContent += temp
            results = []
            realTimeFactor = re.findall(r'Timing stats: real-time factor for offline decoding was (.*?) = ', fileContent)
            results.append(realTimeFactor)
            transcription = re.findall(r'utterance-id1 (.*?)\n', fileContent)
            transcriptionList = []
            for item in transcription:
                if(len(item) > 1000):
                    transcriptionList.append(item)
            results.append(transcriptionList)
            transcriptionName = re.findall(r'Output #0, wav, to (.*?):', fileContent)
            results.append(transcriptionName)
            return results
        except Exception as e:
                Tools.writeException("nohupTranscriptionContent", e)
        return False


    def fileTranscriptionContent(filePath):
        """
        This parses the content of the transcription file. The size of the file can basically be unlimited
        but each line has to be under 300000 characters(?). This then returns the following...\n\n
        index 0 -- url\n
        index 1 -- name\n
        index 2 -- realTimeFactor\n
        index 3 -- transcription\n
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
            url = re.findall(r'URL:(.*?)\n', fileContent)
            name = re.findall(r'name:(.*?)\n', fileContent)
            results.append(url)
            results.append(name)
            realTimeFactor = re.findall(r'Timing stats: real-time factor for offline decoding was (.*?) = ', fileContent)
            results.append(realTimeFactor)
            transcription = re.findall(r'utterance-id1 (.*?)\n', fileContent)
            for item in transcription:
                if(len(item) > 1000):
                    results.append(item)
            if((len(results[0]) > 0) and (len(results[1]) > 0) and (len(results[2]) > 0) and (len(results[3]) > 0)):
                return results
            else:
                return False
        except Exception as e:
                Tools.writeException("fileTranscriptionContent", e)
        return False

        



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
            if(Tools.numRunningProcesses == 0):
                subprocess.run("rm -r ./" + folderName + "/*", shell=True)
                return True
            else:
                return False
        except Exception as e:
                return False


    def downloadMp3(url, fileName):
        """
        downloads the mp3 from the url (doesn't include .mp3) 
        to a file in the podcasts folder with the .mp3 tag (does not initially include .mp3).\n\n 
        
        this then calls convertToWav to convert the file into the correct format
        """
        try:
            with urllib3.PoolManager().request("GET", url + ".mp3", preload_content=False) as resp, open("./podcasts/" + fileName + ".mp3", 'wb') as out_file:
                copyfileobj(resp, out_file)
            resp.release_conn()
            return True
        except:
            return False

    
    def convertToWav(fileName):
        """
        the argument requires the filename is without the .mp3 part. This properly converts the .mp3 to .wav with the proper format for aspire models
        """
        try:
            subprocess.run("ffmpeg -i ./podcasts/" + fileName + ".mp3 -acodec pcm_s16le -ac 1 -ar 8000 ./podcasts/" + fileName + ".wav", shell=True)
            subprocess.run("rm ./podcasts/" + fileName + ".mp3", shell=True)
            return True
        except Exception as e:
            Tools.writeException("convertToWav",e)
            return False


    def runTranscription(fileName):
        """
        runs the transcription given the .wav file name. The wav must have the correct .wav format and is in 8000khz (?)
        """
        try:
            subprocess.Popen("nohup ./online2-wav-nnet3-latgen-faster --online=false --do-endpointing=false --frame-subsampling-factor=3 --config=online.conf --max-active=7000 --beam=15.0 --lattice-beam=6.0 --acoustic-scale=1.0 --word-symbol-table=words.txt final.mdl HCLG.fst 'ark:echo utterance-id1 utterance-id1|' 'scp:echo utterance-id1 ./podcasts/" + fileName + ".wav|' 'ark:/dev/null' >> ./transcripts/" + fileName + ".txt &", shell=True)
            return True
        except Exception as e:
            Tools.writeException("runTranscription",e)
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
        errorFile.write("ERROR occured in " + className + " with the following message\n" + str(exceptionString) + "\n\n")
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






class DatabaseInteract:
    """
    This is where the database is updated. Refer to the example clips/header for format information.\n\n
    Seeding the database would include the usage of 'insertHeader' then 'insertClips'. Pretty much every 
    function in here will require a dbConnection argument
    """
    def insertHeader(dbConnection, content):
        """
        Inserts a header for a podcast. Needs to be completed before insertClips
        is started \n\n
        Needs data for --> Homepage, Name, Description, Category, Source, SocialWeb, twitter, Facebook\n
        Returns true if successful or false if not
        """
        try:
            Homepage = Omny.parseInit(content, "HomePage")
            Name = Omny.parseInit(content, "Name")
            Description = Omny.parseInit(content, "Description")
            Category =  Omny.parseInit(content, "Category")
            Source = Omny.parseInit(content, "Source")
            Web = Omny.parseInit(content, "Web")
            Facebook = Omny.parseInit(content, "twitter")
            twitter = Omny.parseInit(content, "Facebook")
            cursor = dbConnection.cursor()
            cursor.execute("""INSERT INTO podcasts(homepage, name, description, category, source, imageuri, web, twitter, Facebook, lastupdated) VALUES(%s, %s, %s, %s, %s, NULL, %s, %s, %s, NULL);""", (Homepage, Name, Description, Category, Source, Web, twitter, Facebook,))
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
		        Tools.writeException("insertHeader", "e")
        return False


    def insertClips(dbConnection, content):
        """
        Insert clips. Cant do this without 'Podcast' exsiting because
        of foreign key reasons\n
        returns true if successful or false if not.
        """
        try:
            cursor = dbConnection.cursor()
            for item in content:
                podcastName = Omny.parseInit(item, "PodcastName")
                Title = Omny.parseInit(item, "Title")
                AudioUrl = Omny.parseInit(item, "AudioUrl")
                Date = Omny.parseInit(item, "Date").split(" ")
                Duration = Omny.parseInit(item, "Duration")
                stripTime = datetime.strptime(Date[0] + " " + Date[1] + " " +  Date[2], "%b %d, %Y")
                parsedDate = str(stripTime.month) + "-" + str(stripTime.day) + "-" + str(stripTime.year)
                cursor.execute("INSERT INTO transcriptions(audiourl, timeperword, podcastname, transcription, description, date, title, duration, pending) VALUES('" + AudioUrl + "', NULL, '" + podcastName + "', NULL, NULL, '" + parsedDate + "', '" + Title + "', '" + Duration + "', FALSE);")
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
		        Tools.writeException("insertClips", e)
        return False
    

    def updateDescription(dbConnection, description, audiourl):
        """
        updates the description given the audiourl & the description you want to update it to
        """
        try:
            cursor = dbConnection.cursor()
            parsedDescription = description.replace("'", "")
            cursor.execute("UPDATE transcriptions SET description = '" + parsedDescription + "' WHERE audiourl = '" + audiourl + "';")
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
		        Tools.writeException("updateDescription", e)
        return False
    
    
    def uploadTranscriptionData(dbConnection, url, name, timePerWord, transcription):
        """
        This is to be used after the parseTranscriptionContent function if it was successful.
        \n\nIt basically uploads the arguents to the database, returning false and throwing an 
        error if unsuccesful (or true otherwise)\n
        """
        try:
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE transcriptions SET name = '" + name + "', timeperword = '" + timePerWord + "', transcription = '" + transcription + "' WHERE audiourl = '" + url + "';")
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            Tools.writeException("uploadTranscriptionData", e)
        return False
    
    
    def uploadTranscriptionDataModified(dbConnection, name, timePerWord, transcription):
        """
        u fucked up
        """
        try:
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE transcriptions SET timeperword = '" + timePerWord + "', transcription = '" + transcription + "' WHERE title LIKE '%" + name + "%';")
            dbConnection.commit()
            cursor.close()
            return True
        except Exception as e:
            Tools.writeException("uploadTranscriptionData", e)
        return False


    def checkPre(dbConnection):
        """
        checks the database for empty transcription entries, returns a list with \n\n
        index 0 = audiourl
        index 1 = title
        """
        cursor = dbConnection.cursor()
        cursor.execute("select audiourl, title from transcriptions WHERE COALESCE(description, '') = '' AND pending = FALSE LIMIT 1;")
        entry = cursor.fetchone()
        cursor.close()
        cursor = dbConnection.cursor()
        cursor.execute("UPDATE transcriptions SET pending = TRUE WHERE audiourl = '" + entry[0] + "';")
        dbConnection.commit()
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
        




class Omny:
    """
    This class tracks the fields required to populate both the 'Podcasts' and the basic elements
    for the 'transctiptions' table in the database
    """
    def getContent(url, replaceHeader):
        """ 
        This class makes the URL request and returns a slightly more cleaned
        up version of the content. \n\n
        
        The content still includes the header so the next step is using either
        the 'parse' or 'parseAfterHeader' function.
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763', 'Host': 'omny.fm'}
            req = requests.get(url, headers=headers)
            soup = BeautifulSoup(req.text, 'html.parser')
            if(replaceHeader):
                return str(soup.findAll(attrs={"type":"text/javascript"})[2].text).replace("\n", "").replace("window.preloadedShow = ", "").replace("\t", "")
            return soup
        except Exception as e:
            Tools.writeException("updateDescription", e)
            return False
        

    def getFile(filePath):
        """
        This is for entering a podcast entry into the database \n\n
        The json should be split up into a header file with the same fields that normal headers have
        as well as a Clip file with the same fields that normal clips have
        """
        jsonFile = open(filePath, "r")
        return json.loads(jsonFile.read(9999999))
    
    def parseInit(content, element):
        """
        To be used after you load the header using "getFile", this allows you to parse the file\n\n
        Header --> Homepage, Name, Description, Category, Source, SocialWeb, twitter, Facebook \n
        ClipName --> PodcastName, Title, AudioUrl, Date, Duration
        """
        return content[element]
    # Examples (test cases)
    # Omny.parseHeader(stuff, "Name")
    # Omny.parseHeader(stuff, "Description")
    # Omny.parseHeader(stuff, "Category")
    # Omny.parseHeader(stuff, "SocialWeb")
    # Omny.parseHeader(stuff, "Facebook")
    # Omny.parseHeader(stuff, "twitter")
    def parseHeader(content, header):
        """
        Valid parse strings include...\n\n
        Header --> Name, Description, Category, SocialWeb, twitter, Facebook, Title \n\n
        I do not advise you to parse anything outside of the fields listed above in this function. \n
        Use 'parseClips' if you're trying to parse individual clips/shows
        \n\n returns the single occurence of the input string
        """
        return re.findall(r'\"' + header + '\":\"(.*?)\",', content)[0]
    


    def parseClips(content, clipName):
        """
        Valid parse strings include...\n\n
        ClipName --> Title, Description, AudioUrl, PublishedUtc \n \n
        You can't parse the header with this function. Use parseHeader if you want to do that
        \n\n returns an array of all occurences of the input string
        """
        content = content.split("\"Clips\":[{")[1]
        if(clipName == "PublishedUtc"):
            return re.findall(r'\"' + clipName + '\":\"(.*?)T', content)
        return re.findall(r'\"' + clipName + '\":\"(.*?)\",', content)


