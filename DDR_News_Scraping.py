#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import time
import re
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
import http.cookiejar
import os 
import sys
import ijson
import io
from bson.code import Code
import json
import string
from datetime import datetime
from nltk.corpus import stopwords
from datetime import datetime
import re 
import matplotlib.pyplot as plt
from textblob import TextBlob
from datetime import datetime
import re 
import pandas as pd
from pandas import DataFrame
import random
import numpy as np


# ### 1.Scrape Nasdaq to get all the news link, title and dynamic api link

# In[3]:


#The website url does not get the data by get request, it calls an api which can be found by inspecting
headers = {
"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
"Accept-Encoding":"gzip, deflate",
"Accept-Language":"en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
"Connection":"keep-alive",
"Host":"www.nasdaq.com",
"Referer":"http://www.nasdaq.com",
"Upgrade-Insecure-Requests":"1",
'User-agent': 'Mozilla/5.0'} 

result_links=[]
result_titles=[]
for pg in range(1,2): #page number, can be changed 
    api_url = 'https://www.nasdaq.com/api/v1/search?q=tesla&offset='+str((pg-1)*10)  # get dynamic api link
    response=requests.get(api_url,headers=headers)
    json_result = json.loads(response.content) #the result is a json file 
    html_result=json_result['items'] #parse the json file 
    no_of_result=0 #count number of result 
    for el in html_result:
        time.sleep(3) 
        soup=BeautifulSoup(el,'html.parser')  ##parse the html beautifully
        no_of_result=no_of_result+1
        #print(no_of_result," results") ##to help debugging
        
        #find each search result title,link, and timestamp
        result_title_tag=soup.select("h2.search-result__title>a")[0] 
        result_title=result_title_tag.get("title")
        partial_link=result_title_tag.get("href") #link is only partial
        try:
            date_stamp_string=re.search(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',partial_link)[0]
            date_stamp=datetime.strptime(date_stamp_string, '%Y-%m-%d') #transfer to date object
            date_stamp_bchmark=datetime.strptime('2019-10-01','%Y-%m-%d') #2019.10.01 is the time stock price start to soar
        except:
            continue
        
        #skip the symbol results which are not news
        result_eyebrow=soup.select("div.search-result__eyebrow")[0]
        #skip the ones that are not news or the ones that are earlier than 2019.10.01
        if result_eyebrow.text!="Symbols" and date_stamp>=date_stamp_bchmark: 
            full_link="https://www.nasdaq.com"+str(partial_link)
            result_links.append(full_link)
            result_titles.append(result_title)
            print(result_title)
            print(full_link)
    if response.status_code!=200:
        raise ValueError("Invalid Response Received From Webserver")
    #print(result)


# ## 2. download the links 

# In[4]:


#need to get the cookie 
session_requests = requests.session()
# going to the home page while logged in  
r2=session_requests.get('https://www.nasdaq.com/',headers=headers)
cookie=r2.cookies.get_dict()
print("cookie is :",cookie)

for link in result_links:
    ##download each html  GET requests
    response=requests.get(link,cookies=cookie,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser') 
#   print(soup)
#   write file
    no_of_news=result_links.index(link)
    title=str(result_titles[no_of_news]).translate(str.maketrans(' ','_',string.punctuation))
    with open("tesla_news_"+str(no_of_news+1)+"_"+str(title)+".htm","w",encoding='utf-8') as file:
        html_unicode=UnicodeDammit(str(soup)).unicode_markup
        file.write(html_unicode)


# ## 3. Parse and get the content of the news 

# In[372]:


#a typical leftover thing : [<time class="timestamp__date" datetime="">Feb 13, 2020 7:47AM EST</time>]


# In[2]:


paragraph_list=[]
date_list=[]
directory = os.getcwd() #get the directory
for filename in os.listdir(directory):
    paragraph=""
    if filename.endswith('.htm') == False:
        continue
    try:
        with open(os.path.join(directory, filename), 'r',encoding="utf-8") as file:
            text = file.read()
            soup = BeautifulSoup(text, 'html.parser') 
            #print(soup)
            #get paragraph
            paragraphs = soup.findAll('p') 
        if not paragraphs:
            paragraph=None
        else:
            #print(filename)
            try:
                datestr=soup.select('time[datetime]')[0]['datetime']
                #datestamp
                clean_date=datestr[0:datestr.rfind('-')] #strip out the clean date time
                datetime_object = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%S')
                date_list.append(datetime_object.date()) # get only the date
                #print(datetime_object.date())
                for el in paragraphs[1:]: #first <p> label is meaningless
                    if el.text=="The views and opinions expressed herein are the views and opinions of the author and do not necessarily reflect those of Nasdaq, Inc.":
                        break
                    paragraph=paragraph+el.text
                    #print(el.text) 
                paragraph_list.append(paragraph)
            except:
                #Some news doesn't have value for datetime tag 
                datestr=""
               
    except:
        print("file "+filename,sys.exc_info()[0])


# In[3]:


##There are 814 html file but some are skipped bcs they don't have datetime stamp 
##To see if paragraph and date has the same number of items
print('There are ',len(paragraph_list),'paragraphs and',len(date_list),'date stamps')


# In[61]:


sums=[]
date_sentim_pair=dict()
for pa in paragraph_list:
    sum=0
    blob=TextBlob(pa)
    for sentence in blob.sentences:
        sentim=sentence.sentiment.polarity
        sum=sum+sentim
    i=paragraph_list.index(pa)
    sentim_avg=sum/len(blob.sentences)
    print(date_list[i])
    print(sentim_avg)
    #average sentiment 
    date_sentim_pair[date_list[i]]=sentim_avg


# In[685]:


date_parag_pair=dict()
for pa in paragraph_list:
    i=paragraph_list.index(pa)
    date_parag_pair[date_list[i]]=pa
#print(random.choice(list(date_parag_pair.items())))
print(random.sample(date_parag_pair.items(),1)) #choose a random sample to check

