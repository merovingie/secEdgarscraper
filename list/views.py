from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from .models import Company, Statement, Statment_element_headers, Statement_element_section, Statement_element_data
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import requests
import re
from edgar import edgar as ed
import sys

def home(request):
    companyz = Company.objects.all()
    statementz = Statement.objects.all()
    return render(request, 'list/home.html', context={'companyz': companyz, 'statementz':statementz})

# Create your views here.

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)        
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view

class Createlisting(generic.CreateView):
    model = Company
    fields = ['ticker']
    template_name = 'list/create_list.html'
    success_url = reverse_lazy('home')
    queryset = Company.objects.filter(name='')
    edgar = ed.Edgar()

    def form_valid(self, form):
        #get user and validate form
        form.instance.user = self.request.user
        super(Createlisting, self).form_valid(form)

        #get Company CIK
        tik = form.data['ticker']
        URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
        CIK_RE = re.compile(r'.*CIK=(\d{10}).*')
        f = requests.get(URL.format(tik), stream = True)
        results = CIK_RE.findall(f.text)
        if len(results):
            cik = results[0]

        cmp_name = self.edgar.getCompanyNameByCik(cik)
        
        #create object in database
        company = Company(ticker=tik, cik=cik, name=cmp_name, user=self.request.user)
        company.save()
        
        
        

        # delete empty database
        queryset = Company.objects.filter(name='').delete()

        

        # Creating filename and url structure
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(BASE_DIR, 'static')
        out_path = path + "/sec_edgar_filings/" + tik + "/10-K/"
        
        # creating object of class with path to the download and downloading the txt file which is too big to load without xml iteration && should look for alternative option than that
        dl = Downloader(path)

        # download the latest one by adding the 1
        dl.get_10k_filings(tik, 1)

        #removing the - and .txt to get the number to the current filing submission accession number
        file_name = [f for f in os.listdir(out_path) if os.path.isfile(os.path.join(out_path, f))]
        switched_filename = file_name[0]
        switched_filename = switched_filename.replace('-', '').replace('.txt', '/index.json')


        # creating base url configuration, i can do a better job than this!!!
        bare_url = r"https://www.sec.gov/Archives/edgar/data/"
        base_url = r"https://www.sec.gov"
        documents_url = bare_url + str(results[0]) + "/" + switched_filename
 

        #retreieve the files and get the summary
        content = requests.get(documents_url).json()

        for file in content['directory']['item']:
            
            # Grab the filing summary and create a new url leading to the file so we can download it.
            if file['name'] == 'FilingSummary.xml':

                xml_summary = base_url + content['directory']['name'] + "/" + file['name']
                
                #print info
                print('-' * 50)
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

        # loop through each report in the 'myreports' tag but except the last one it produces an error.
        for report in reports.find_all('report')[:-1]:


            # create a dictionary to store all the different parts we need.
            report_dict = {}
            report_dict['name_short'] = report.shortname.text
            report_dict['name_long'] = report.longname.text
            report_dict['position'] = report.position.text
            report_dict['menu_category'] = report.menucategory.text
            report_dict['url'] = base_url + report.htmlfilename.text

            # append the dictionary to the master list.
            master_reports.append(report_dict)
            if report_dict['name_short'] == 'Consolidated Statements of Cash Flows':

                # print the info.
                print('-'*50)
                print(base_url + report.htmlfilename.text)
                print(report.longname.text)
                print(report.shortname.text)
                print(report.menucategory.text)
                print(report.position.text)

                # creating a holder for the url since a Bug creating a different file path into the database!
                redirect_url_to_statement = base_url + report.htmlfilename.text
                
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
                print('-'*50)
                print(report_dict['name_short'])
                print(report_dict['url'])
                
                statements_url.append(report_dict['url'])
        
        statement = Statement(year=2019, type="CONSOLIDATED STATEMENTS OF CASH FLOWS", url=redirect_url_to_statement ,company=company)
        statement.save()

        statements_data = []

        # loop through each statement url
        for statementUrl in statements_url:

            # define a dictionary that will store the different parts of the statement.
            statement_data = {}
            statement_data['headers'] = []
            
            statement_data['sections'] = []
            
            statement_data['data'] = []
           
            
            # request the statement file content
            content = requests.get(statementUrl).content
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

            #Creating DAtA into Database
            #Creating each header and rotating thru all data values
            print("HEADERSSSSS   ")
            print("Saving Headers...")
            for i in range(len(statement_data['headers'][1])):
                print(statement_data['headers'][1][i])
                statementHeader = Statment_element_headers(field=statement_data['headers'][1][i], statement=statement)
                statementHeader.save()
                print("DATAAAAAAAA   ")
                print("Saving Data Element...")
                for j in statement_data['data']:
                    print(j)
                    print(j[i+1])
                    k = j[i+1]
                    # Optimizing the Data Format
                    if '$' or ',' or '(' in k:
                        k = k.replace('$','')
                        k = k.replace(' ','')
                        k = k.replace(',', '.')
                        k = k.replace('(','-')
                        k = k.replace(')', '')
                        k = float(k)
                        print(k)
                    statementData = Statement_element_data(key = j[0], value=k, statement=statement, company=company, header=statementHeader) 
                    statementData.save()
                        
                    print(j)
                    
                    print("Saving Data Done for Element")
            print("Saving Headers Done")


            print("SECTIONSSSS   ")
            print("Saving Headers ...")
            for i in statement_data['sections']:
                print(i)
                statementSections = Statement_element_section(fieldName=i, statement=statement)
                statementSections.save()
            print("Saving Sections Done...")

           



            # append it to the master list for future analysis with Panda streams and NLP
            statements_data.append(statement_data)

        # print(statements_data)
        
        return redirect('home')
    
     
class Detaillisting(generic.DetailView):
    model = Company
    template_name = 'list/detail_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(Detaillisting, self).get_context_data(*args, **kwargs)
        context['all_statements'] = Statement.objects.all()
        context['all_data'] = Statement_element_data.objects.all()
        print("hi there")
        print(context)
        return context
