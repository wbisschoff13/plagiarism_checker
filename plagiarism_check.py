from bs4 import BeautifulSoup
import pathlib
import mosspy
import os
import easygui
import re
import csv
import py7zr

minimum_matching_percentage = 50
minimum_matching_lines = 40


def getNameFromPath(path):
    # JOHN_DOE_(12345678)
    x = re.findall(r"\w*\d{8}\w*", path)
    # return first value if a match is found, otherwise return the path (minus the first 6 parts)
    if x:
        return x[0]
    else:
        p = pathlib.Path(path.split(" ")[0])
        return p.relative_to(*p.parts[:6])


def getPercentFromString(string):
    # (100%)
    x = re.findall(r"\((\d*)\%\)", string)
    return x


# MOSS settings
USER_ID = 784591462
m = mosspy.Moss(USER_ID, "cc")
m.setIgnoreLimit = 13
m.setNumberOfMatchingFiles = 1000
path = easygui.diropenbox()
name = os.path.basename(path) + " Plag"
print(path)
print(name)

count = 0

file_list = []
ignore_list = ["comments.txt", "timestamp.txt", "Data.txt", "Data - copy.txt", "moss.txt", "ValidNumbers.txt",
               "InvalidNumbers.txt", "moss_files.txt", "Numbers.txt", "objectdb", "config.py", "Output.txt"]

for root, dirs, files in os.walk(path):
    # extract all the compressed files before adding to list
    for file in files:
        f_path = os.path.join(root, file)
        if (file.endswith(".zip") or file.endswith(".rar") or file.endswith(".7z")):
            try:
                Archive(f_path).extractall(root)
            except:
                print("Could not extract", f_path)
    for file in files:
        f_path = os.path.join(root, file)
        if not file in ignore_list:
            if file.endswith(".cpp") or file.endswith(".c"):
                # print(f_path)
                count += 1
                m.addFile(f_path)
                file_list.append(f_path)

# add this file if a template/assistance was given
# m.addBaseFile(os.path.join(path, "base.py"))

print("Sending Report Of Size: ", count)
# Submission Report URL
url = m.send()

print("Report Url: " + url)

# Save report file
print(os.path.join(path, name))
m.saveWebPage(url, os.path.join(path, name))
print(os.path.join(path, "..",  name))
# Download whole report locally including code diff links
mosspy.download_report(url, os.path.join(path, "..",  name), connections=8)

# print main url again
print("Report Url: " + url)

# -----------------------------------------------------------
# scraping starts here
print("MOSS Complete, scraping")

page = os.path.abspath(os.path.join(path, "..",  name, "index.html"))
soup = BeautifulSoup(open(page), 'html.parser')
data = []
names = []

for section in soup.find_all('tr'):
    count = 0
    temp = []
    percent = 0
    lines = 0
    n = ""
    for link in section.find_all('td'):
        count += 1
        value = link.get_text()
        if count < 3:
            num = int(getPercentFromString(value)[0])
            if num > percent:
                percent = num
            n = getNameFromPath(value.strip())
            temp.append(n)
        else:
            lines = int(value.strip())
            temp.append(percent)
            temp.append(lines)
    if lines > minimum_matching_lines and percent > minimum_matching_percentage:
        names.append(n)
        data.append(temp)

print("Scraping Complete")

# save to a .csv for further processing in Excel, might implement processing in Python at a later stage
with open(os.path.join(path, '..', name + ".csv"), "w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Filename', 'Filename', 'Plag %', 'Lines'])
    for f1, f2, plag, lines in data[1:]:
        writer.writerow([f1, f2, plag, lines])

print("Saved to", os.path.join(path, "..", name + ".csv"))
