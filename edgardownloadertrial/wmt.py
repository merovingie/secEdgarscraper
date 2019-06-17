from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import requests
import re
import edgar
import sys

# sys.setrecursionlimit(30000)

# creating object of class with path to obslute download
input_ticker = "WMT"
path = "/home/merovingie/PycharmProjects/Sec-Scrap/secscrap/edgardownloadertrial"
out_path = path + "/sec_edgar_filings/" + input_ticker + "/10-K/"
print(out_path)
dl = Downloader(path)
# download the latest one
dl.get_10k_filings(input_ticker, 1)

# # create soup object
# soup = BeautifulSoup(open("/home/merovingie/PycharmProjects/Sec-Scrap/secscrap/edgardownloadertrial/sec_edgar_filings/WMT/10-K/0000104169-19-000016.txt"))
# print(soup.prettify())

DEFAULT_TICKERS = [input_ticker]
URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
CIK_RE = re.compile(r'.*CIK=(\d{10}).*')

# change Ticker into CIK
cik_dict = {}
for ticker in DEFAULT_TICKERS:
    f = requests.get(URL.format(ticker), stream = True)
    results = CIK_RE.findall(f.text)
    if len(results):
        cik = str(results[0])
        cik_dict[str(ticker).upper()] = str(results[0])
print(cik_dict)

# Use edgar to get text compilation of the lxml
# Get Company name from CIK
edgar1 = edgar.Edgar()
cmp_name = edgar1.getCompanyNameByCik(results[0])
print(cmp_name)
company = edgar.Company(cmp_name, cik)

# Creating filename and url structure
file_name = [f for f in os.listdir(out_path) if os.path.isfile(os.path.join(out_path, f))]
switched_filename = file_name[0]
switched_filename = switched_filename.replace('-', '').replace('.txt', '/index.json')
print(switched_filename)
print(file_name)

bare_url = r"https://www.sec.gov/Archives/edgar/data/"
base_url = r"https://www.sec.gov"
documents_url = bare_url + str(results[0]) + "/" + switched_filename
print(documents_url) 

#retreieve the files and get the summary
content = requests.get(documents_url).json()

for file in content['directory']['item']:
    
    # Grab the filing summary and create a new url leading to the file so we can download it.
    if file['name'] == 'FilingSummary.xml':

        xml_summary = base_url + content['directory']['name'] + "/" + file['name']
        
        print('-' * 100)
        print('File Name: ' + file['name'])
        print('File Path: ' + xml_summary)

# define a new base url that represents the filing folder. This will come in handy when we need to download the reports.
base_url = xml_summary.replace('FilingSummary.xml', '')

# request and parse the content
content = requests.get(xml_summary).content
soup = BeautifulSoup(content, 'lxml')

# find the 'myreports' tag because this contains all the individual reports submitted.
reports = soup.find('myreports')

# I want a list to store all the individual components of the report, so create the master list.
master_reports = []

# loop through each report in the 'myreports' tag but avoid the last one as this will cause an error.
for report in reports.find_all('report')[:-1]:


    # let's create a dictionary to store all the different parts we need.
    report_dict = {}
    report_dict['name_short'] = report.shortname.text
    report_dict['name_long'] = report.longname.text
    report_dict['position'] = report.position.text
    report_dict['category'] = report.menucategory.text
    report_dict['url'] = base_url + report.htmlfilename.text

    # append the dictionary to the master list.
    master_reports.append(report_dict)
    if report_dict['name_short'] == 'Consolidated Statements of Cash Flows':

        # print the info to the user.
        print('-'*100)
        print(base_url + report.htmlfilename.text)
        print(report.longname.text)
        print(report.shortname.text)
        print(report.menucategory.text)
        print(report.position.text)
        
# in case of multiple statements
statements_url = []

for report_dict in master_reports:
    
    # define the statements we want to look for.
    item1 = r"Consolidated Statements of Cash Flows"
    
    # store them in a list.
    report_list = [item1]
    
    # if the short name can be found in the report list.
    if report_dict['name_short'] in report_list:
        
        # print some info and store it in the statements url.
        print('-'*100)
        print(report_dict['name_short'])
        print(report_dict['url'])
        
        statements_url.append(report_dict['url'])

statements_data = []

# loop through each statement url
for statement in statements_url:

    # define a dictionary that will store the different parts of the statement.
    statement_data = {}
    statement_data['headers'] = []
    statement_data['sections'] = []
    statement_data['data'] = []
    
    # request the statement file content
    content = requests.get(statement).content
    report_soup = BeautifulSoup(content, 'html')

    # find all the rows, figure out what type of row it is, parse the elements, and store in the statement file list.
    for index, row in enumerate(report_soup.table.find_all('tr')):
        
        # first let's get all the elements.
        cols = row.find_all('td')
        
        # if it's a regular row and not a section or a table header
        if (len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0): 
            reg_row = [ele.text.strip() for ele in cols]
            statement_data['data'].append(reg_row)
            
        # if it's a regular row and a section but not a table header
        elif (len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0):
            sec_row = cols[0].text.strip()
            statement_data['sections'].append(sec_row)
            
        # finally if it's not any of those it must be a header
        elif (len(row.find_all('th')) != 0):            
            hed_row = [ele.text.strip() for ele in row.find_all('th')]
            statement_data['headers'].append(hed_row)
            
        else:            
            print('We encountered an error.')

    # append it to the master list.
    statements_data.append(statement_data)

print(statements_data)



# # Get Url for With Searching Paramters for the required files
# # thinking about using urllib and requests to parse the returned html from search but the result will cause memory segementation error either way! 
# url_com = company.getFilingsUrl(filingType="10-k")
# print(url_com)
# # retrieving a text document file of the lxml of the required 10-k file
# tree = company.getAllFilings(filingType= "10-k", noOfEntries=1)
# docs = edgar.getDocuments(tree, noOfDocuments=1)
# print(type(docs))
# # saving file to disk for sanity check!:)
# p = open("wmt.txt", "w")
# p.write(docs)
# p.close()

# # USING REGEX AND OTHER METHODS TO PERPARE THE DOCUMENTS!
# docstr = tostring(docs)
# # data = docs.decode("utf-8").split("Consolidated Statements of Cash Flows")
# print(docstr)
# # for 'Consolidated Statements of Cash Flows' in docs:



