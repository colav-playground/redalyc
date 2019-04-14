QUALITY=True
try:
   import Levenshtein # pip3 install python-levenshtein
except ImportError:
    QUALITY=False
import re
from bs4 import BeautifulSoup
import requests
#import getpass
import json
import pandas as pd
import sys
import time
import random


url='https://scholar.google.com'

import requests
headers_Get = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }


#import googlescholar as gs
#%%writefile ../cienciometria/googlescholar.py

def firefox_get(url):
    r=requests.Session()
    rget=r.get(url,headers=headers_Get)
    
    html = rget.text
    if html.lower().find('gs_captcha_f')>-1:
        sys.exit('ERROR: Captcha anti-robots requested!\n Aborting execution.')

    return html

def get_google_scholar(record):
    '''
    Analyise the BeautifulSoup record for an article 
    in Google Scholar.
    Output is a Python dictionary with keys: 
    'title', 'authors','profiles','Jornal','Year',
    'abstract','cites','cites_link'
    '''
    import random
    import time
    gsr={}
    try:
        cites=record.find_all('a',{"href":re.compile( "/scholar\?cites=" )})[0]
        try:
            gsr['cites']=int( cites.text.split()[-1] )
            gsr['cites_link']=cites.attrs.get('href')
        except:
            gsr['cites']=0
    except:
        cites=None

    # Title
    try:
        #The .split('XXX')[-1]  does not afect the result when .text does no contains 'XXX'
        tc=record.find_all('h3',{"class":"gs_rt"})[0].text.split('[CITATION][C] ')[-1]
    except:
        tc=''

    gsr['title']=tc.strip().split('[HTML][HTML] ')[-1].split(
                                  '[PDF][PDF] '  )[-1]
    
    # Explore authors, google scholar profile - Journal, Year - Publisher
    gpa=None
    try:
        gpa=record.find_all('div',{"class":"gs_a"})[0]
        #Full ref with authors, google scholar profile - Journal, Year - Publisher
        ref=gpa.text
        gsr['ref']=ref.strip()
        refparts=ref.split('\xa0-')
    except IndexError:
        gsr['ref']=''
        refparts=[]

    try:
        gsr['authors']=refparts[0]
    except IndexError:    
        gsr['authors']=''
        
    try:
        journalparts=refparts[-1].strip().split(' - ')
        gsr['publisher']=journalparts[-1]
        gsr['Journal']=journalparts[0].split(',')[0]
        gsr['Year']=journalparts[0].split(',')[-1].strip()
    except IndexError:
        gsr['publisher']=''
        gsr['Journal']=''
        gsr['Year']

    #Abstract:
    try:
        gsr['abstract']=record.find_all('div',{'class':'gs_rs'})[0].text.replace('\xa0…','')
    except:
        gsr['abstract']=''
    # profiles
    if gpa:
        lpr=gpa.find_all("a",{ "href":re.compile("/citations\?user=*")   } )
        prf={}
        for pr in lpr:
            prf[ pr.text ]=pr.attrs.get('href').split('?')[-1].split('&')[0].split('user=')[-1]
        gsr['profiles']=prf
    
    time.sleep( random.randint(1,3)  ) # avoid robots
    return gsr

def request_google_scholar_url(url):
    return requests.get(url)

def google_scholar_page(html):
    '''
    Convert a Google Scholar page into a list
    of dictionaries with metadata info
    '''
    if html.lower().find('gs_captcha_f')>-1:
        input('check robots')
   
    soup = BeautifulSoup(html, "html.parser")
    rgs=soup.find_all('div', {'class':'gs_ri' })

    citations=[]
    for record in rgs:
        citations.append( get_google_scholar(record) )
        
    return citations

def google_scholar_query(title='', author='', coauthors=[], DOI='', year=0, publisher='',
                         journal='', volume='', issue='', pages=0,
                         DEBUG=False):
    '''
    Search Google scholar with `sholar_lookup` full fields.
    Only the first result is analized. The output includes 
    a quality measurements between the query and the results 
    Output is a Python dictionary with keys: 
    'title', 'authors','profiles','cites','cites_link',
    'quality_title','quality_author'
    '''
    gs={}
    # + → %2B in query formula:
    baseurl='https://scholar.google.com/'
    q='scholar_lookup?'
    
    nl=0
    if title:
        nl=nl+1
        q= q+'title={}'.format(title.replace(' ','+'))
    if author:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'author={}'.format(author.replace(' ','+'))
    if DOI:
        if nl: q= q+'&'
        nl=nl+1    
        q= q+'doi={}'.format(DOI)
    if year:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'year={}'.format(year)
    if publisher:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'publisher={}'.format(publisher.replace(' ','+'))
    if journal:
        if nl: q= q+'&'
        nl=nl+1     
        q= q+'journal={}'.format(journal.replace(' ','+'))
    if volume:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'volume={}'.format(volume)
    if issue:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'issue={}'.format(issue)   
    if pages:
        if nl: q= q+'&'
        nl=nl+1
        q= q+'pages={}'.format(pages)
    if coauthors:
        for i in coauthors :
            if nl: q= q+'&'
            nl=nl+1
            q= q+'author={}'.format(i.replace(' ','+'))    
    url=baseurl+q
    if DEBUG:
        print(url)   
    
    #s = requests.Session()
    rtext=firefox_get(url)

    #soup = BeautifulSoup(r.text, "html.parser")
    soup = BeautifulSoup(rtext, "html.parser")


    # Main contents:
    rgs=soup.find_all('div', {'class':'gs_ri' })

    try:
        record=rgs[0]
    except IndexError:
        #exit if record not found and returns empty dictionary
        return gs
    
    gs.update(get_google_scholar(record))
    
    #Check if author is in authors list
    if gs and author:
        sau=0
        for a in gs['authors'].split(','):
            if QUALITY:            
               saun=Levenshtein.ratio(author.lower(),a.lower().strip())
            else:
               saun=0
            if saun>sau:
                sau=saun
                
        gs['quality_author']=round(sau,2)
    else:
        gs['quality_author']=-1 #-1 means not checked
        
    if gs and title:
        if QUALITY:    
            gs['quality_title']=round( Levenshtein.ratio(
                   title.lower(),gs['title'].lower() ),2 )
        else:
            gs['quality_title'] =-1 #-1 means not checked
    else:
        gs['quality_title'] =-1 #-1 means not checked
        
    #EXTRA FIELDS:
    #PDF
    try:
        gs['PDF']=soup.find_all('div',
                        {"class":"gs_or_ggsm"})[0].find_all('a')[0].get("href")
    except:
        gs['PDF']=''


    if DEBUG:
        print('='*80)
        print(record)
        
        return gs,record
    else:
        return gs

def get_cites_refs(browser,url,maxcites=65,t=60):
    """
    WARNING: Works only with SELENIUM true
    """
    import random
    import time
    url='https://scholar.google.com'+url
    browser.get(url)
     
    endpage=int(maxcites/10)+1
    refs=''
    
    kk=google_scholar_page( browser.page_source )
    try:
        refs=refs+'\n'.join( list((pd.DataFrame(kk)['title']+'; '
                                  +pd.DataFrame(kk)['ref']).values) )+'\n' 
    except:
        refs=''
    
    
    for i in range(endpage):
        try:
            browser.find_element_by_class_name('gs_ico_nav_next').click()
            kk=google_scholar_page( browser.page_source )
            try:
                refs=refs+'\n'.join( list( (pd.DataFrame(kk)['title']+'; '
                                +pd.DataFrame(kk)['ref']).values ) )+'\n' 
            except:
                refs=''
        except:
            break
            
    time.sleep(random.uniform(0.9*t,1.1*t))
    return refs

def main(nini,nend,apikey):
    n=nend-nini                
    T=12 #hours of search
    t=T/n*3600 # [s] query time
    t=60
    day=24*3600 #s
    mintime=0.9*t*n # [s] minimal time search
    wait=30#day-mintime # maximum wait
                    
    
    #See https://stackoverflow.com/questions/36837663/reading-json-file-as-pandas-dataframe-error
    r = requests.get('http://fisica.udea.edu.co:8080/data?init={}&end={}&apikey={}'.format(
           nini,nend+1,apikey)) # Fix bug in API
    df=pd.DataFrame(json.loads(r.text)).fillna('').reset_index(drop=True)
    datos=df.copy()

    doi='DOI'
    title_simple='TITULO'
    article_id='IDARTICULO'
    dfgs=pd.DataFrame()
    ibrkn=0
    maxibrn=400

    for ii in datos[nini:nend].index:
        print(ii,datos.loc[ii,doi])
        #gsd=google_scholar_query(DOI=doi)
        gsd=google_scholar_query(title=datos.loc[ii,title_simple].replace('\n',' '),
                        author=datos.loc[ii,'Autor(es)'].split(', ')[0].strip(),
                        coauthors=datos.loc[ii,'Autor(es)'].split(', ')[1:4],
                        DOI=datos.loc[ii,doi],
                        year=datos.loc[ii,'ANIO'],
                        journal=datos.loc[ii,'REVISTA'],
                        volume=datos.loc[ii,'VOLUMEN'],
                        issue=datos.loc[ii,'NUMERO'],
                        pages=datos.loc[ii,'PAGINAS'])

        gsd['old_title']=datos.loc[ii,'TITULO']
        gsd['DOI']=datos.loc[ii,'DOI']
        gsd['ID_ARTICLE']=datos.loc[ii,article_id]
        dfgs=dfgs.append(gsd,ignore_index=True )
        dfgs.to_json('rdlyc_{}_{}.json'.format(nini,nend))
        time.sleep(random.uniform(0.9*t,1.1*t))
        
#======BEGIN Graphical mode (Self contained)============
#FROM https://www.python-course.eu/tkinter_entry_widgets.php
#from redalyc import *
GUI=True
try:
    from tkinter import *
    import tkinter.messagebox
except ImportError:
    print('WARNING:\n try sudo apt-get install python3-tk\n for GUI mode.')
    prnt('Going to text mode..')
    GUI=False
        

fields = ('Initial article', 'Final article', 'API key')
def makeform(root, fields):
    entries = {}
    for field in fields:
        row = Frame(root)
        lab = Label(row, width=22, text=field+": ", anchor='w')
        ent = Entry(row)
        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)
        ent.pack(side=RIGHT, expand=YES, fill=X)
        #Relevant dictionary
        entries[field] = ent
    return entries

def runcommand(entries):
    nini=int( entries['Initial article'].get() )
    nend=int( entries['Final article'].get() )
    apikey=entries['API key'].get()
    main(nini,nend,apikey) # main console mode
    tkinter.messagebox.showinfo(message='Finished! Upload output:\n rdlyc_{}_{}.json'.format(nini,nend))

def maingui():
    root = Tk()
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e=ents: fetch(e)))   
    b1 = Button(root, text='Seach Google Scholar (output in console)',
          command=(lambda e=ents: runcommand(e)))
    b1.pack(side=LEFT, padx=5, pady=5)
    b3 = Button(root, text='Quit', command=root.quit)
    b3.pack(side=LEFT, padx=5, pady=5)
    root.mainloop()
        

#======END Graphical mode ============

def run():
    #GUI=False #DEBUG purposes
    if GUI:
        maingui()
    else:
        import sys
        if len(sys.argv)<4:
            sys.exit('USAGE: {} N_ini N_end API_key'.format(sys.argv[0]))
            
        nini=int( sys.argv[1] )
        nend=int( sys.argv[2] )
        apikey=sys.argv[3]#getpass.getpass('Api key')
        main(nini,nend,apikey) 
        print( 'Finished! Upload output:\n rdlyc_{}_{}.json'.format(nini,nend) )

if __name__ == "__main__":
    run()
