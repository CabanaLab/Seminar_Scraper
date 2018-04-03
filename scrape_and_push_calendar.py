import os
import localsettings as ls

# Google API stuff
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# Web Parser stuff
from bs4 import BeautifulSoup, SoupStrainer
import urllib.request
from itertools import count
from urllib.parse import urlencode, urlparse, parse_qs
from lxml.html import fromstring
from requests import get

# Calendar stuff
from datetime import datetime, timedelta
import pytz
import logging

# Set up logging
logging.basicConfig(
    filename=ls.log_file,
    level=logging.DEBUG,
    filemode="a",
    format='%(asctime)s │ %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

logging.getLogger("googleapiclient.discovery_cache").propagate = False
logging.getLogger("googleapiclient").setLevel(logging.CRITICAL)

log = logging.getLogger('scrape_and_push_calendar')
formatter = logging.Formatter('%(name)s - %(asctime)s | %(message)s')

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/urlshortener'
]
CLIENT_SECRET_FILE = ls.client_secret_file
APPLICATION_NAME = 'CGSA Calender'

# Set localsettings
tzinfo=pytz.timezone('America/Chicago')
calendarId = ls.calendarId

# Mini function to remove unnecessary white space
collapse = lambda s: " ".join(s.split()) or (lambda s: s)

def get_credentials():
    """
    Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(
        credential_dir,
        'calendar-quickstart.json'
    )

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_seminar_links():
    """Search through URLs and provide a list of URLs that contain
    valid seminar data"""
    n = count(1)
    links_list = []
    while True:
        resp = urllib.request.urlopen("http://chem.uic.edu/seminars/" + str(next(n)))
        soup = BeautifulSoup(resp, from_encoding=resp.info().get_param('charset'))

        for para in soup.find_all('p'):
            if 'Sorry, there are no future events' in para.get_text():
                return links_list

        for link in soup.find_all('a', href=True):
            if 'http://chem.uic.edu/events/' in link['href']:
                log.debug('Event Found! %s', link['href'])
                links_list.append(link['href'])

def get_title(source):
    """Returns event title"""
    return source.find('h1').get_text()

def get_date(source):
    """Returns event date"""
    return collapse(source.find('p', "event-date").get_text())

def get_time(source):
    """Returns event time"""
    return collapse(source.find('p', 'event-time').get_text())

def get_location(source):
    """Returns event location"""
    _location = source.find(string='Location').find_parent().find_next_sibling().get_text()
    _address = source.find(string='Address').find_parent().find_next_sibling().get_text()
    return collapse(_location + ',' + _address)

def get_host(source):
    """Returns seminar host"""
    return collapse(source.find(string='Contact').find_parent().find_next_sibling().get_text())

def get_description(source):
    """Returns seminar description """
    return collapse(source.find('div', "_details u-definition-list--table").find_next_sibling().p.get_text())

def get_created(source):
    """Returns event creation date"""
    return collapse(source.find(string='Date posted').find_parent().find_next_sibling().get_text())

def get_modified(source):
    """Returns date event was last modified"""
    return collapse(source.find(string='Date updated').find_parent().find_next_sibling().get_text())

def datetimeify(date, time, created, modified, tzinfo=pytz.timezone('America/Chicago')):
    """Turn string dates into datetime objects"""
    _dstart = str(date + ' ' + time).split('-')[0].rstrip()
    _dend = date + str(time.split('-')[1].rstrip())

    dt_dstart = datetime.strptime(_dstart, "%B %d, %Y %I:%M %p")
    dt_dend = datetime.strptime(_dend, "%B %d, %Y %I:%M %p")
    dt_created = datetime.strptime(created, "%b %d, %Y")
    dt_modified = datetime.strptime(modified, "%b %d, %Y")

    return dt_dstart, dt_dend, dt_created, dt_modified

def fix_broken_times(_dtstart, _dtend):
    """Sometimes there are input errors on the website. This checks
    for errors and tries to correct them"""
    # Does the event end before it starts?
    if _dtstart > _dtend:
        # Too early/late for working hours?
        log.debug('Event ends before it starts. Fixing...')
        if _dtstart.hour < 7:
            _dtstart += timedelta(hours=12)
            log.debug('Event starts too early. Switching AM --> PM')
        elif _dtstart.hour > 19:
            _dtstart -= timedelta(hours=12)
            log.debug('Event starts too late. Switching PM --> AM')
        if _dtend.hour < 7:
            _dtend += timedelta(hours=12)
            log.debug('Event ends too early. Switching AM --> PM')
        elif _dtend.hour > 19:
            _dtstart -= timedelta(hours=12)
            log.debug('Event ends too late. Switching PM --> AM')
    return _dtstart, _dtend

def bring_me_soup(link):
    """Provide the URL and return the scraped html soup"""
    resp = urllib.request.urlopen(link)
    soup = BeautifulSoup(resp, from_encoding=resp.info().get_param('charset'))
    return soup.find(lambda tag: tag.name == 'article' and tag.get('class') == ["post-type-event"])





def URL(title,http=False):
    if title[0:12] == 'Seminar with' or title[0:12] == 'seminar with':
        string=title[13:len(title)]     
    if title[0:12] != 'Seminar with' and title[0:12] != 'seminar with' and title.find('Prof')!=-1:
        string=title[title.find('Prof'):len(title)]
    if title[0:12] != 'Seminar with' and title[0:12] != 'seminar with' and title.find('Prof')==-1:
        string=False

    #log.debug('URL string: %s', string)
	
    try:
        newstring=string.replace(" ", "+")
        raw = get("https://www.google.com/search?q="+newstring).text
        page = fromstring(raw)



        results=[]
        for result in page.cssselect(".r a"):
            url = result.get("href")

            if url.startswith("/url?"):
                url = parse_qs(urlparse(url).query)['q']
            results.append(url[0])

        first=results[0].find('/')
        second=results[0].find('.com')

        if first >1 and second<0:
            output=short(results[0],http=http)
        else:

            if first <1 or second>0:
                first=results[1].find('/')
                second=results[1].find('.com')
                if first >1 and second<0:
                    output=short(results[1],http=http)
                    log.debug('Link found: %s', output)
            else:
                output='Link Not Avaliable'
    except:
        output='Link Not Avaliable'
    return output




def short(url, http=False):
    """Shorten the URL using Google API"""
    if http == False:
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
    shortener = discovery.build('urlshortener', 'v1', http=http).url()

    # Create request
    body = {
        'longUrl': url
    }

    return shortener.insert(body=body).execute()['id']

def main():
    # Log in to the Google Calendar API
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar','v3',http=http)
    log.debug("Received credentials from Google API")

    links_list= get_seminar_links()

    for link in links_list:

        # Start a blank dict
        info = {}

        # Parse the webpage
        html_event = bring_me_soup(link)

        # Put the required information into a dict
        info['title'] = get_title(html_event)
        info['date'] = get_date(html_event)
        info['time'] = get_time(html_event)
        info['location'] = get_location(html_event)
        info['description'] = get_description(html_event)
        info['created'] = get_created(html_event)
        info['modified'] = get_modified(html_event)
        info['url'] = link
        info['host'] = get_host(html_event)

        #log.debug("Title: %s", info['title'])

        #log.debug("Will URL: %s", URL(info['title']))

        # Put start and end dates in correct datetime format
        _dtstart, _dtend, _dtcreated, _dtmodified = datetimeify(
            info['date'],
            info['time'],
            info['created'],
            info['modified']
        )

        # Check for time entry errors
        _dtstart, _dtend = fix_broken_times(_dtstart, _dtend)

        # Pack the event
        event = {
            'summary': info['title'],
            'location': info['location'],
            'description': info['description'] + '\n\nHost: ' + info['host'] + '\n\n' + URL(info['title'], http=http),
            'source': {
                'url': info['url'],
                'title': "This event was automatically created from chem.uic.edu/seminars",
            },
            'start': {
                # isoformat makes it JSON parseable
                'dateTime': _dtstart.isoformat(),
                'timeZone': tzinfo.zone,
            },
            'end': {
                # isoformat makes it JSON parseable
                'dateTime': _dtend.isoformat(),
                'timeZone': tzinfo.zone,
            },
            # iCalUIC is required otherwise we have to check for an
            # existing uid and update() if it exists. A handy trick...
            'iCalUID': str(datetime.strftime(_dtstart, '%Y%m%d%H%M%S') + '/' + datetime.strftime(_dtend,  '%Y%m%d%H%M%S')),
        }

        log.debug("Event Packed")
        imported_event = service.events().import_(calendarId=calendarId, body=event).execute()
        log.debug("Exported to %s", short(imported_event['htmlLink'], http=http))

if __name__ == "__main__":
    main()
