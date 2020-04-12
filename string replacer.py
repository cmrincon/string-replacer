import os
import sys
import getopt
from shutil import copyfile
from threading import Thread
from time import sleep

def restore(folderPath,subdirectories):
    dir = os.chdir(folderPath)
    fileList = os.listdir(dir)

    for fileName in fileList:
        cpltFileName = os.path.join(folderPath,fileName)
        
        if os.path.isdir(cpltFileName) and subdirectories:
            restore(cpltFileName,subdirectories)
        
        elif fileName[-4:] == '.bak':
            encryptedFileName = encryptString(fileName[:-8]) + fileName[-8:-4]
            encryptedPath = os.path.join(folderPath,encryptedFileName)
            if (os.path.exists(encryptedPath)):
                os.remove(encryptedPath)
            os.rename(cpltFileName,cpltFileName[:-4])        
           

def encryptString(string):
    encrString = ''
    for letter in string:
        if letter >='z' or letter < 'A' or (letter >= 'Z' and letter < 'a') :
            encrString = encrString + letter
        else:
            byString = letter.encode()
            intString = int.from_bytes(byString, byteorder='little', signed = False)
            
            intString = intString + 1
           
            byString = intString.to_bytes(1,byteorder='little', signed = False)
            encrLetter = byString.decode()
            encrString = encrString + encrLetter
    return encrString

def segCopy(folderPath,subdirectories):
    dir = os.chdir(folderPath)
    fileList = os.listdir(dir)

    for fileName in fileList:
        cpltFileName = os.path.join(folderPath,fileName)
        
        if os.path.isdir(cpltFileName) and subdirectories:
            segCopy(cpltFileName,subdirectories)
        
        elif (fileName[-4:] == '.dll') or (fileName[-4:] == '.exe') or (fileName[-4:] == '.lua'):
        #elif (fileName[-4:] == '.dll') or (fileName[-4:] == '.exe'):
            fileNameOut = cpltFileName + '.bak'
            copyfile(cpltFileName,fileNameOut)

def getDllExeList(folderPath,subdirectories):
    
    targetFiles = list()
    dir = os.chdir(folderPath)
    fileList = os.listdir(dir)
    
    for fileName in fileList:
        cmplFiName = os.path.join(folderPath,fileName)
       
        if os.path.isdir(cmplFiName) and subdirectories:
            targetFiles = targetFiles + getDllExeList(cmplFiName,subdirectories)
        
        elif (cmplFiName[-4:] == '.dll') or (cmplFiName[-4:] == '.exe') or (cmplFiName[-4:] == '.lua'):
        #elif (cmplFiName[-4:] == '.dll') or (cmplFiName[-4:] == '.exe'):
            fileDict = {'path': folderPath, 'filename': fileName}
            targetFiles.append(fileDict)
    
    return targetFiles

def make2StringSameSize(string1,string2):
#Returns string2 truncated to the length of string1
    
    size1 = len(string1)
    size2 = len(string2)
    
    if size1 > size2:
        string2 = string2.ljust(size1,'\x00')
    elif size1 < size2:
        string2 = string2[:size1 - 1]
    
    return string2


def replaceFolder(folderPath,subdirectories=False,optOld = [],optNew = []):

    if not os.path.exists(folderPath):
        raise FileNotFoundError("Directory not found: " + folderPath)
    
    segCopy(folderPath,subdirectories)
    
    enOptOld = [x.encode() for x in optOld]
    #enOptOldSize = [len(x) for x in optOld]
    #optNewSize = [len(x) for x in optNew]
    enOptNew = [make2StringSameSize(x,y).encode() for (x,y) in zip(optOld,optNew)] #Make 2 strings of the same size and encode it
    
    dllExeList = getDllExeList(folderPath,subdirectories)
    for entry in dllExeList:

        originalFileNamePath = os.path.join(entry['path'],entry['filename'])
        
        with open(originalFileNamePath,'rb') as fileIn:
            fileBuff = fileIn.read()
            
        for entry2 in dllExeList:

            if entry2['filename'] != entry['filename']:

                if (entry2['filename'][-4:] != '.lua'): #Not lua file.

                    enNewFileName = (encryptString(entry2['filename'][:-4]) + entry2['filename'][-4:]).encode()
                    enOldFileName = entry2['filename'].encode()
                    fileBuff = fileBuff.replace(enOldFileName, enNewFileName)


                    enNewFileName = (encryptString(entry2['filename'][:-4])).encode()
                    enOldFileName = entry2['filename'][:-4].encode()
                    fileBuff = fileBuff.replace(enOldFileName, enNewFileName)
                else: #lua file.
                    pass             
            
            for (oldBytes, newBytes) in zip(enOptOld,enOptNew):
                fileBuff = fileBuff.replace(oldBytes,newBytes)

        newOutputFileName = encryptString(entry['filename'][:-4]) + entry['filename'][-4:]
        with open(os.path.join(entry['path'], newOutputFileName),'wb') as fileOut:
            fileOut.write(fileBuff)
        os.remove(originalFileNamePath)


def parseOptionals(listString):
    
    oldFileName = []
    newFileName = []
    for string in listString:

        splitedString = string.split('->') 
        
        if len(splitedString) == 2:
            oldFileName.append(splitedString[0])
            newFileName.append(splitedString[1])    

        else: raise SyntaxError("You must use <optional Dir 1>-><optional Dir 2>")
    return (oldFileName,newFileName)


if __name__ == "__main__":    
    
    optionDirectory = False
    optionRestore = False
    optionSubDirectories = False

    argvSize = len(sys.argv)
    if argvSize > 1:
        options, optionals = getopt.gnu_getopt(sys.argv[1:],'d:rs', [])

        for opt,arg in options:
            
            if opt == '-d':
                optionDirectory = True
                path = arg
            
            optionRestore = True if opt == '-r' else optionRestore
            
            optionSubDirectories = True if opt == '-s' else optionSubDirectories

        if optionDirectory:
            normPath = os.path.normpath(path)
            if optionRestore:
                print("Restoring " + normPath,end='')
                threadTarget = restore
                threadArgs= (normPath,optionSubDirectories)                
                
            else:
                print("Replacing " + normPath,end= '')
                threadTarget = replaceFolder
                optionalsList = parseOptionals(optionals)
                threadArgs=(normPath,optionSubDirectories,optionalsList[0],optionalsList[1]) 

            workThread = Thread(target = threadTarget,args=threadArgs)
            workThread.start()
            while True:
                sleep(2)
                print('.', end='')
                if not workThread.is_alive(): break
            print()
            print("Done!")

        else:
            print("Incorrect number of arguments or not defined a target directory.")

