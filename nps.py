## proj_nps.py
## Skeleton for Project 2, Winter 2018
## ~~~ modify this file, but don't rename it ~~~
import requests
import json
from bs4 import BeautifulSoup
import secrets_example
import plotly.plotly as py
import pandas as pd

# on startup, try to load the cache from file
CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}

def make_request_using_cache(url):
    unique_ident = url

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]
directory_dict={}


def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}={}".format(k, params[k]))
    return baseurl + "&".join(res)

def get_lat_lng_from_text_search(site):
    name=site.name
    park_type=site.type.lower().replace(" ","+")
    park_name=site.name.lower().replace(" ","+")
    myapi=secrets_example.google_places_key
    params1={"query":park_name+"+"+park_type,"key":secrets_example.google_places_key,"radius":"10000"}
    baseurl1="https://maps.googleapis.com/maps/api/place/textsearch/json?"
    page_text = make_request_using_cache(params_unique_combination(baseurl1, params1))
    result = json.loads(page_text)['results']
    if result:
        geometry=result[0]['geometry']
        location=geometry['location']
        lat=str(location['lat'])
        lng=str(location['lng'])
        name=site.name
        return [lat,lng]
    else:
        return "fail to get lat lng"

def get_list_from_nearby_search(lat,lng):
    params2={"location":lat+","+lng,"key":secrets_example.google_places_key,"radius":"10000"}
    baseurl2="https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
    page_text = make_request_using_cache(params_unique_combination(baseurl2, params2))
    results_list = json.loads(page_text)['results']
    nearby_places=[]
    for each in results_list:
        name=each['name']
        geometry=each['geometry']
        location=geometry['location']
        lat=str(location['lat'])
        lng=str(location['lng'])
        nearby_place=NearbyPlace(name,lat,lng)
        nearby_places.append(nearby_place)
    return nearby_places


## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NationalSite():
    def __init__(self, type, name, desc, url=None):
        self.type = type
        self.name = name
        self.description = desc
        self.url = url

    def init_from_details_url(self,details_url):
        page_text = make_request_using_cache(details_url)
        page_soup=BeautifulSoup(page_text,'html.parser')
        vcard=page_soup.find(class_='vcard')
        # needs to be changed, obvi.
        self.address_street =vcard.find(itemprop="streetAddress" ).text.strip()
        self.address_city = vcard.find(itemprop="addressLocality").text.strip()
        self.address_state = vcard.find(class_='region').text.strip()
        self.address_zip = vcard.find(class_='postal-code').text.strip()

    def __str__(self):
        str_=self.name+" ("+self.type+"): "+self.address_street+", "+self.address_city+", "+self.address_state+" "+self.address_zip
        return str_



## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NearbyPlace():
    def __init__(self, name,lat,lng):
        self.name = name
        self.lat=lat
        self.lng=lng

    def get_lat_lng_name(self):
        return [self.lat,self.lng,self.name]

    def __str__(self):
        str_=self.name
        return str_

## Must return the list of NationalSites for the specified state
## param: the 2-letter state abbreviation, lowercase
##        (OK to make it work for uppercase too)
## returns: all of the NationalSites
##        (e.g., National Parks, National Heritage Sites, etc.) that are listed
##        for the state at nps.gov
def get_sites_for_state(state_abbr):
    baseurl = 'https://www.nps.gov'
    state_url=baseurl+"/state/"+state_abbr
    page_text = make_request_using_cache(state_url)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    content_div = page_soup.find_all(class_='col-md-9 col-sm-9 col-xs-12 table-cell list_left')
    #each=page_soup.find(class_='col-md-9 col-sm-9 col-xs-12 table-cell list_left')
    national_sites=[]
    for each in content_div:
        park_type=each.find('h2').string
        park_name=each.find('h3').string
        park_description=each.find('p').string
        park_url=baseurl+each.find('h3').find('a')['href']
        national_site=NationalSite(park_type,park_name,park_description,park_url)
        national_site.init_from_details_url(park_url)
        national_sites.append(national_site)
    return national_sites


## Must return the list of NearbyPlaces for the specifite NationalSite
## param: a NationalSite object
## returns: a list of NearbyPlaces within 10km of the given site
##          if the site is not found by a Google Places search, this should
##          return an empty list
def get_nearby_places_for_site(national_site):
    nearby_places=[]
    if get_lat_lng_from_text_search(national_site)!="fail to get lat lng":
        lat_lng=get_lat_lng_from_text_search(national_site)
        lat=lat_lng[0]
        lng=lat_lng[1]
        nearby_places=get_list_from_nearby_search(lat,lng)
    return nearby_places

## Must plot all of the NationalSites listed for the state on nps.gov
## Note that some NationalSites might actually be located outside the state.
## If any NationalSites are not found by the Google Places API they should
##  be ignored.
## param: the 2-letter state abbreviation
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_sites_for_state(state_abbr):
    lat_vals = []
    lon_vals = []
    text_vals = []
    national_sites=get_sites_for_state(state_abbr)
    for national_site in national_sites:
        if get_lat_lng_from_text_search(national_site)!="fail to get lat lng":
            lat_lng=get_lat_lng_from_text_search(national_site)
            lat=lat_lng[0]
            lng=lat_lng[1]
            lat_vals.append(lat)
            lon_vals.append(lng)
            text_vals.append(national_site.name)

    data = [ dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = lon_vals,
            lat = lat_vals,
            text = text_vals,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'star',
            ))]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]
    layout = dict(
            title = 'National Park<br>(Hover for park names)',
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center= {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )
    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename=state_abbr+' - natural park' )


## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a plotly page in the web browser
def plot_nearby_for_site(site_object):
    center_lat_vals = []
    center_lon_vals = []
    center_text_vals = []
    nearby_lat_vals = []
    nearby_lon_vals = []
    nearby_text_vals = []
    if get_lat_lng_from_text_search(site_object)!="fail to get lat lng":
        lat_lng=get_lat_lng_from_text_search(site_object)
        lat=lat_lng[0]
        lng=lat_lng[1]
        center_lat_vals.append(lat)
        center_lon_vals.append(lng)
        center_text_vals.append(site_object.name)
        nearby_places=get_list_from_nearby_search(lat,lng)
        for nearby_place in nearby_places:
            result=nearby_place.get_lat_lng_name()
            lat=result[0]
            lng=result[1]
            name=result[2]
            nearby_lat_vals.append(lat)
            nearby_lon_vals.append(lng)
            nearby_text_vals.append(name)

    trace1 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = center_lon_vals,
            lat = center_lat_vals,
            text = center_text_vals,
            mode = 'markers',
            marker = dict(
                size = 20,
                symbol = 'star',
                color = 'red'
            ))
    trace2 = dict(
            type = 'scattergeo',
            locationmode = 'USA-states',
            lon = nearby_lon_vals,
            lat = nearby_lat_vals,
            text = nearby_text_vals,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'circle',
                color = 'blue'
            ))
    data = [trace1, trace2]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in nearby_lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in nearby_lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    layout = dict(
            title = site_object.name+'<br>its nearby sites',
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(100, 217, 217)",
                countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center = {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )
    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename=site_object.name+'and its nearby place' )

if __name__ == "__main__":
    term= input('Enter command (or "help" for options):')
    while term!="exit":
        if term == "help":
            print("""
            list <stateabbr>
               available anytime
               lists all National Sites in a state
               valid inputs: a two-letter state abbreviation
           nearby <result_number>
               available only if there is an active result set
               lists all Places nearby a given result
               valid inputs: an integer 1-len(result_set_size)
           map
               available only if there is an active result set
               displays the current results on a map
           exit
               exits the program
           help
               lists available commands (these instructions)
            """)
        elif "list" in term:
            state_abbr=term.split(" ")[1]
            national_sites=get_sites_for_state(state_abbr)
            n=1
            for national_site in national_sites:
                print(n,end=" ")
                print(national_site)
                n+=1
            term= input('Enter command (or "help" for options):')
            while(("list" not in term) and term!="exit" and term!="map"):
                if "nearby" in term:
                    site_num=int(term.split(" ")[1])
                    if len(national_sites)<1:
                        print("There is no result")
                    else:
                        nearby_places=get_nearby_places_for_site(national_sites[site_num-1])
                        n=1
                        for nearby_place in nearby_places:
                            print(n,end=" ")
                            print(nearby_place)
                            n+=1
                        term= input('Enter command (or "help" for options):')
                        if term=="map":
                            print("This is the map for sites nearby" + national_sites[site_num-1].name)
                            plot_nearby_for_site(national_sites[site_num-1])
                        else:
                            print("Incorrect Command. You can use nearby + number or map.")
                term= input('Enter command (or "help" for options):')
            if term=="map":
                print("This is the map for sites in state")
                plot_sites_for_state(state_abbr)
            elif term=="exit":
                break
            else:
                print("Incorrect Command.")
        elif "nearby" in term or "map" == term:
            print("Please use list <stateabbr> command first. Enter 'help' for details. ")
        else:
            print("Incorrect command.")

        term= input('Enter command (or "help" for options):')

    print("Bye!")
