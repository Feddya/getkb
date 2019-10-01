import sys

import hashlib

import re

import json

import requests
from bs4 import  BeautifulSoup
from bs4 import Tag


import base64
def _downloadFile(url, digest):

    fileName = url.split("/")[-1]
    digestDecoded = base64.b64decode(digest)

    print("\tDownloading to file {}".format(fileName))

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        sha1 = hashlib.sha1()

        with open(fileName, "wb") as f:
            for chunk in r.iter_content(chunk_size=100000):
                if chunk:

                    sha1.update(chunk)

                    f.write(chunk)
                    #print("write")

        if sha1.digest() == digestDecoded:
            print("\tDigest matches.")
        else:
            print("\tDigest not matches.")
    pass


def _getDownloadLink(updateId):
    url = "http://www.catalog.update.microsoft.com/DownloadDialog.aspx"
    jparams = {
                "size": 0,
                "languages":"",
                "uidInfo": updateId,
                "updateID" : updateId
            }
    jjparams = json.dumps(jparams)
    data = {
            "updateIDs" : "["+jjparams+"]",
        }

    downloadDialog = requests.post(url, data)

    # url in javascript code only, not in html
    # downloadInformation[0].files[
    #     0].url = 'http://download.windowsupdate.com/c/msdownload/update/software/secu/2016/12/windows6.1-kb3207752-ia64_122dbd2ed83c9cd2320cd9c693834325e9e67e92.msu';
    urlStr = None
    url = re.search("(http://.*msu)", downloadDialog.text)
    if url:
        urlStr = url.group(0)
    # downloadInformation[0].files[0].digest = 'Ei29Ltg8nNIyDNnGk4NDJenmfpI=';
    digestStr = None
    digest = re.search("digest = '(.*)';", downloadDialog.text)
    if digest:
        digestStr = digest.group(1)

    return (urlStr, digestStr)


def downloadUpdate(updateName, isX64 = True, windowsVersion="Windows 7"):

    if updateName == "":
        return

    link = "http://www.catalog.update.microsoft.com/Search.aspx?q=KB{}".format(updateName)

    print("Searching for update '{}'".format(updateName))

    r = requests.get(link)
    str = r.text

    s = BeautifulSoup(str, features="html.parser")
    table = s.findAll(attrs={"id":"tableContainer", "class":"resultsBackGround"})
    if not table:
        print("\tSearch dialog format changed. Aborting")
        return

    t1 = s.select("#headerRow")
    foundIDs = []
    for line in t1[0].next_siblings:

        if not isinstance(line, Tag):
            continue

        archMatch = True
        if isX64 and "x64" not in line.contents[2].text:
            archMatch = False

        osMatch = True
        if windowsVersion not in line.contents[3].text:
            osMatch = False

        if archMatch and osMatch:
            buttons = line.findAll('input', attrs={'type':'button', 'value':'Download'})
            if len(buttons):
                id = buttons[0]["id"]
                print("\tFound id '{}'".format(id))
            foundIDs.append(id)


    links = []
    for id in foundIDs:
        link, digest = _getDownloadLink(id)
        print("\tFor id '{}' \n\t\tfound link '{}',\n\t\tdigest '{}'".format(id, link, digest))
        links.append((link, digest))

    for ld in links:
        _downloadFile(*ld)


def downloadUpdates(updatesListFile):

    with open(updatesListFile, "rt") as f:
        s = f.readlines()
        updates = set(s)

    for update in updates:
        downloadUpdate(update.lower().replace("kb", "").strip())

def main(argv):

    if not argv:
        print("Usage getkb.py <file with updates list>")
        return

    downloadUpdates(argv[0])

    pass

if __name__ == "__main__":
    main(sys.argv[1:])