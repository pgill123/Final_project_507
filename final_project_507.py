import requests
import sys
import urllib
import json
import sqlite3
import csv
import json
import codecs
import sys

import plotly.plotly as py
import plotly.graph_objs as go

# from initialize_db import *
from yelp_secret import *
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

city_db = 'city_food.db'

STATECSV = 'U.S._Chronic_Disease_Indicators__CDI_.csv'
CITYCSV = '500_Cities__Local_Data_for_Better_Health__2017_release.csv'

CACHE_FILENAME = "SI507finalproject_cache.json"
CACHE = None

######################
# Define Functions to
# Populate DB
######################

#drops tables from the data base
#params: db_name, type (json or csv)
#returns: none
def drop_table(db_name, type):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    try:
        if type == "csv":
            drop_State_raw = '''
                DROP TABLE IF EXISTS 'State_raw';
            '''
            cur.execute(drop_State_raw)
            conn.commit()

            drop_City_raw = '''
                DROP TABLE IF EXISTS 'City_raw';
            '''
            cur.execute(drop_City_raw)
            conn.commit()

        elif type == "json":
            drop_yelp = '''
                DROP TABLE IF EXISTS 'Yelp_raw';
            '''
            cur.execute(drop_yelp)
            conn.commit()
        else:
            print("Invalid type entered. Please select json or csv.")
    except:
        print("Table does not exist. Can only drop existing tables. Use print_db_contents() to see what is currently in the db.")

#initializes the database with three main tables that will be manipulated later
# -yelp api pull, and city and state public health data sets
#params: db_name, type (json or csv)
#returns: none
def init_db(db_name, type):
    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
    except Error as e:
        print(e)

    try:
        if type == "csv":
            create_state = '''
                    CREATE TABLE 'State_raw' (
                                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                                'YearEnd' INTEGER,
                                'LocationAbbr' TEXT,
                                'Question' TEXT,
                                'DataValueAlt' INTEGER,
                                'DataValueType' TEXT,
                                'Stratification' TEXT
                    );
                    '''
            cur.execute(create_state)
            conn.commit()


            create_city = '''
                    CREATE TABLE 'City_raw' (
                                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                                'Year' INTEGER,
                                'StateAbbr' TEXT,
                                'CityName' TEXT,
                                'Measure' TEXT,
                                'DataValueTypeID' TEXT,
                                'Data_Value' INTEGER
                     );
                    '''
            cur.execute(create_city)
            conn.commit()

        elif type == "json":
            #last three rows are populated later
            create_yelp = '''
                    CREATE TABLE 'Yelp_raw' (
                                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                                'Name' TEXT,
                                'Category' TEXT,
                                'Price' TEXT,
                                'Rating' REAL,
                                'ReviewCount' INTEGER,
                                'City' TEXT,
                                'State' TEXT,
                                'Latitude' REAL,
                                'Longitude' REAL,
                                'price_grp' TEXT,
                                'Rating_grp' TEXT,
                                'Review_grp' TEXT

                    );
                    '''
            cur.execute(create_yelp)
            conn.commit()
        else:
            print("Type does not exist. Please chose either json or csv.")

    except:
        print("Table already exist. Please drop before creating.")


######################
# Define Functions to
# View DB and table contents
######################
#prints the variable names and first ten records of a selected table
def print_table_contents(db_name, table_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = 'SELECT *  FROM ' + table_name
    cur.execute(q)
    meta = cur.description

    print("Meta:\n")
    for i in meta:
        print("\t",i[0])


    q = 'SELECT *  FROM ' + table_name
    cur.execute(q)
    view_table =  cur.fetchall()
    count = 1
    print("Contents:\n")
    for i in view_table:
        print("\t",i)
        count+=1
        if count == 10:
            break

def print_table_all(db_name, table_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = 'SELECT *  FROM ' + table_name
    cur.execute(q)
    meta = cur.description

    print("Meta:\n")
    for i in meta:
        print("\t",i[0])


    q = 'SELECT *  FROM ' + table_name
    cur.execute(q)
    view_table =  cur.fetchall()
    count = 1
    print("Contents:\n")
    for i in view_table:
        print("\t",i)



#prints all tables in the data base
def print_db_contents(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    pull_tables= "SELECT * FROM sqlite_master WHERE type='table'"
    cur.execute(pull_tables)
    view_tables= cur.fetchall()

    print("All Tables in ", db_name)
    for i in view_tables:
        print("\t",i[1])

######################
# Call to Yelp API and create SQL table
######################

# Standard caching functions
def load_cache_from_file():
    global CACHE
    try:
        f = open(CACHE_FILENAME, 'r')
        CACHE = json.loads(f.read())
        f.close()
        print('Loading cache from:', CACHE_FILENAME)
    except:
        # Cache file does not exist, initialize an empty cache
        print('Initialized an empty CACHE dictionary.')
        CACHE = {}

def save_cache_to_file():
    if CACHE is not None:
        f = open(CACHE_FILENAME, 'w')
        f.write(json.dumps(CACHE))
        f.close()
        print('Saved cache to', CACHE_FILENAME)

def params_unique_combination(baseurl, params_d, private_keys=["api_key"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

#takes a users search request for yelp and creates a json dictionary for inserting into the db
#params: city, state and the programmers api_key from secrets.py
#returns: json dictionary
def get_from_yelp(city, state, api_key = API_KEY):
    headers = {'Authorization': 'Bearer %s' % api_key}
    baseurl_yelp = "https://api.yelp.com/v3/businesses/search"
    params_dict_yelp = {}
    params_dict_yelp["term"] = "restaurants"
    params_dict_yelp["location"] = city + state
    params_dict_yelp["limit"] = 50
    params_dict_yelp["sort_by"] = "review_count"

    ident_yelp = params_unique_combination(baseurl_yelp, params_dict_yelp)

    #if the data is in the cache, just return it and leave the method
    load_cache_from_file()
    if ident_yelp in CACHE:
        print("yelp key in cache. Returning the cached data.")
        return CACHE[ident_yelp]
        #otherwise, request data from api and place in a dictionary
    else:
        print("yelp key not in cache. Requesting data.")
        get_yelp_data = requests.get(baseurl_yelp, headers = headers, params=params_dict_yelp)
        print("Pulled yelp data from here:",get_yelp_data.url)
        dict_yelp = json.loads(get_yelp_data.text)
        #now, cache your yelp data
        CACHE[ident_yelp] = dict_yelp
        save_cache_to_file()
        return dict_yelp

#takes a users search request for yelp and creates the raw Yelp table for later manip
#params: db_name
#returns: none
def insert_json(db_name, city, state):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    drop_table(db_name,"json")
    init_db(db_name, "json")

    #populate everything from the API but use the city name from the user input so that visualization is clean, and don't reflect cities not searched for.
    dict_yelp = get_from_yelp(city, state, api_key = API_KEY)
    for dict in dict_yelp["businesses"]:
        insertion = (dict["name"], dict["categories"][0]["title"],dict["price"],dict["rating"],dict["review_count"], city, dict["location"]["state"],dict["coordinates"]["latitude"],dict["coordinates"]["longitude"])
        insert_statement = 'INSERT INTO "Yelp_raw" '
        insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)'
        cur.execute(insert_statement, insertion)
    conn.commit()

# ######################
# # Read in excel data
# ######################

#takes two csv files and creates the state and city raw tables for alter manip
#params: db_name
#returns: none
def insert_csv(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    drop_table(db_name, "csv")
    init_db(db_name,"csv")

    with open(STATECSV) as f:
        state_list = csv.reader(f)
        for row in state_list:
                insertion = (row[1],row[2],row[6],row[11], row[9], row[17])
                insert_statement = 'INSERT INTO "State_raw" '
                insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?) '
                cur.execute(insert_statement, insertion)
        conn.commit()

    with open(CITYCSV) as f:
        city_list = csv.reader(f)
        for row in city_list:
                insertion = (row[0],row[1],row[3],row[8], row[10], row[12])
                insert_statement = 'INSERT INTO "City_raw" '
                insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?) '
                cur.execute(insert_statement, insertion)
        conn.commit()

# ######################
# # Modify tables and store
# ######################

# modifies the raw Yelp data to have certain categories for tabling
#params: db_name
#returns: none - updates the existing Yelp_raw
def mod_yelp(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = '''
    SELECT
        case when price in ("$") then "Low"
            when price in ("$$", "$$$") then "Medium"
            when price in ("$$$$") then "High"
        end as price_grp
        ,case
            when Rating in (1, 1.5) then "1 star"
            when Rating in (2,2.5) then "2 star"
            when Rating in (3,3.5) then "3 star"
            when Rating in (4,4.5) then "4 star"
            when 5 <= Rating     then "5 star"
        end as rating_grp
        ,case when 0 <= ReviewCount and ReviewCount < 200  then "0 to 199"
            when 200 <= ReviewCount and ReviewCount < 600 then "200  to 599"
            when 600 <= ReviewCount and ReviewCount < 1000 then "600 to 999"
            when 1000 <= ReviewCount then "1,000+"
        end as review_grp
        ,ID
    FROM Yelp_raw
    '''
    cur.execute(q)
    yelp_tuple = cur.fetchall()


    for row in yelp_tuple:
        price_grp = row[0]
        insertion = (row[0], row[1], row[2], row[3])
        insert_statement = 'UPDATE Yelp_raw '
        insert_statement += 'SET price_grp = ? , rating_grp = ? ,review_grp = ? '
        insert_statement += 'WHERE ID = ? '
        cur.execute(insert_statement, insertion)
    conn.commit()

    q = 'SELECT * FROM Yelp_raw'
    cur.execute(q)
    view_table =  cur.fetchall()

    count = 1
    print("Yelp mod:")
    for i in view_table:
        print("\t",i)
        count+=1
        if count == 10:
            break


# adds a user selected city's restaurant information to an existing data set
#params: db_name, whether this is a new cumulative data set (new), or an addition to the existiing one(add)
#returns: none - creates new db to create yelp_resto
def yelp_add(db_name, user_input = "new"):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    if user_input == "new":
        drop_Yelp_resto = '''
            DROP TABLE IF EXISTS 'Yelp_resto';
        '''
        cur.execute(drop_Yelp_resto)
        conn.commit()

        #this table can be updated with additional entries from user. Inteded to accumulate user entries where Yelp_raw is rewritten each time a new api is called
        create_yelp = '''
                CREATE TABLE 'Yelp_resto' (
                            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                            'Name' TEXT,
                            'Category' TEXT,
                            'Price' TEXT,
                            'Rating' REAL,
                            'ReviewCount' INTEGER,
                            'City' TEXT,
                            'State' TEXT,
                            'Latitude' REAL,
                            'Longitude' REAL,
                            'Price_grp' TEXT,
                            'Rating_grp' TEXT,
                            'Review_grp' TEXT
                );
                '''
        cur.execute(create_yelp)
        conn.commit()

        q = '''
        SELECT
            Name
            ,Category
            ,Price
            ,Rating
            ,ReviewCount
            ,City
            ,State
            ,Latitude
            ,Longitude
            ,price_grp
            ,Rating_grp
            ,Review_grp
        FROM Yelp_raw
        '''
        cur.execute(q)
        yelp_tuple = cur.fetchall()


        for row in yelp_tuple:
            insertion = row
            insert_statement = 'INSERT INTO "Yelp_resto" '
            insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(insert_statement, insertion)
        conn.commit()

    elif user_input == "add":
        q = '''
        SELECT
            Name
            ,Category
            ,Price
            ,Rating
            ,ReviewCount
            ,City
            ,State
            ,Latitude
            ,Longitude
            ,price_grp
            ,Rating_grp
            ,Review_grp
        FROM Yelp_raw
        '''
        cur.execute(q)
        yelp_tuple = cur.fetchall()

        for row in yelp_tuple:
            insertion = row
            insert_statement = 'INSERT INTO "Yelp_resto" '
            insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(insert_statement, insertion)
        conn.commit()




# modifies the raw 500 cities data to include the city rate, and then it
# also aggregates over all the 500 cities to get a national equivalent, and a difference between teh
# city and national rates
#params: db_name
#returns: none - creates new db to create city_obesity
def mod_city(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = '''
    SELECT
        max(a.year) as Year
        ,StateAbbr as State
        ,CityName as City
        ,Data_Value as City_rate
        ,round(Nation_rate,1) as Nation_rate
        ,round((Data_Value - Nation_rate),1) as Diff_rate
    FROM City_raw as a
    LEFT OUTER JOIN
            (SELECT
                max(year) as Year
                ,avg(Data_Value) as Nation_rate
                from City_raw
                where DataValueTypeID = "CrdPrv" and CityName <> " " and Measure = "Obesity among adults aged >=18 Years"
            ) as b
    on a.YEAR = b.Year
    where DataValueTypeID = "CrdPrv" and CityName <> " " and Measure = "Obesity among adults aged >=18 Years"
    group by
        StateAbbr
        ,CityName
        ,Nation_rate
    having max(a.year)
    '''
    cur.execute(q)
    city_tuple = cur.fetchall()

    drop_City_Obesity = '''
        DROP TABLE IF EXISTS 'City_Obesity';
    '''
    cur.execute(drop_City_Obesity)
    conn.commit()

    create_city = '''
            CREATE TABLE 'City_Obesity' (
                        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                        'Year' INTEGER,
                        'State' TEXT,
                        'City' references Yelp_raw(City),
                        'City_rate' REAL,
                        'Nation_rate' REAL,
                        'Diff_rate' REAL
             );
            '''
    cur.execute(create_city)
    conn.commit()

    for row in city_tuple:
        insertion = (row[0],row[1],row[2],row[3], row[4], row[5])
        insert_statement = 'INSERT INTO "City_Obesity" '
        insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?) '
        cur.execute(insert_statement, insertion)
    conn.commit()


# modifies the raw state CDC data. Stores an overall, male and female adult obesity rate
#params: db_name
#returns: none - creates new db to create state_obesity
def mod_state(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = '''
    SELECT
        max(YearEnd) as Year
        ,LocationAbbr as State
        ,max(case when Stratification = "Overall" then DataValueAlt end) as State_obesity_rate
        ,max(case when Stratification = "Male" then DataValueAlt end) as State_men_obesity_rate
        ,max(case when Stratification = "Female" then DataValueAlt end) as State_women_obesity_rate
    FROM State_raw
    WHERE LocationAbbr <> "US" and DataValueType = "Crude Prevalence" and Question =  "Obesity among adults aged >= 18 years"
    GROUP BY LocationAbbr
    HAVING max(YearEnd)
    ORDER BY LocationAbbr
    '''
    cur.execute(q)
    state_tuple = cur.fetchall()

    drop_State_Obesity = '''
        DROP TABLE IF EXISTS 'State_Obesity';
    '''
    cur.execute(drop_State_Obesity)
    conn.commit()

    create_state = '''
            CREATE TABLE 'State_Obesity' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Year' INTEGER,
                'State' TEXT,
                'State_obesity_rate' REAL,
                'State_men_obesity_rate' REAL,
                'State_women_obesity_rate' REAL
             );
            '''
    cur.execute(create_state)
    conn.commit()

    for row in state_tuple:
        insertion = (row[0],row[1],row[2],row[3], row[4])
        insert_statement = 'INSERT INTO "State_Obesity" '
        insert_statement += 'VALUES (NULL, ?, ?, ?, ?, ?) '
        cur.execute(insert_statement, insertion)
    conn.commit()



# ######################
# Verify existence of db
# or value in table
# ######################

# determines if the base data base tables exist and if not, populates the db.
# params: database name
# returns: None
def check_csv_exists(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    check_city_exist = '''
        SELECT COUNT(*) from sqlite_master WHERE type = 'table' AND name = 'City_Obesity'
    '''
    cur.execute(check_city_exist)
    city_exist = cur.fetchall()[0][0]


    check_state_exist = '''
        SELECT COUNT(*) from sqlite_master WHERE type = 'table' AND name = 'State_Obesity'
    '''
    cur.execute(check_state_exist)
    state_exist = cur.fetchall()[0][0]

    if city_exist == 0 or state_exist == 0:
        print("Initializing database with city and state information...")
        insert_csv('city_food.db')
        mod_city('city_food.db')
        mod_state('city_food.db')
    else:
        print("Database initialized with city and state information")

# determines if the user selected city is in the city db. if not, user needs to select
# a different city that is captured in the 500 cities project
# params: database name, user selected city
# returns: None
def check_city_exists(db_name, city):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    try:
        q = ' SELECT city '
        q += ' FROM City_Obesity '
        q += ' WHERE city = ' + "'" + city + "'"
        cur.execute(q)
        city_in_db = str(cur.fetchall()[0][0])
        return True
    except:
        return False


def check_yelp_table(db_name, city):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()

        q = ' SELECT count(distinct city) '
        q += ' FROM Yelp_resto'
        cur.execute(q)
        count_city = int(cur.fetchall()[0][0])

        q = ' SELECT count(*) '
        q += ' FROM Yelp_resto '
        q += ' WHERE city = ' + "'" + city + "'"
        cur.execute(q)
        not_in_yelp_db = int(cur.fetchall()[0][0])

        if count_city > 0 and not_in_yelp_db == 0:
            print("City added to Yelp db.")
            return "add"
        elif count_city > 0 and not_in_yelp_db > 0:
            print("City already in db. Use existing information.")

    except:
        print("City initialized new yelp db.")
        return "new"



# ######################
# Functions to data for graphs
# ######################

# creates data for mapping the top 20 restaurants from a user selected city
# params: db_name, city
# returns: list of objects with mapping information stored
class Resto_coordinates():
    def __init__(self, init_tuple):
    	self.long  = init_tuple[2]
    	self.lat   = init_tuple[3]
    	self.name  = init_tuple[0]
    	self.price = init_tuple[1]

    def __str__ (self):
        return "{} with price sign of {} ({}, {})".format(self.name, self.price, self.long, self.lat)

def create_map_list(db_name, city):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = ' SELECT name, price, longitude, latitude '
    q += ' FROM Yelp_resto '
    q += ' WHERE City = ' + "'" + city + "'"
    q += ' LIMIT 20 '

    cur.execute(q)
    yelp_tuple = cur.fetchall()

    map_objects=[]
    for i in yelp_tuple:
        # print(Resto_coordinates(i))
        map_objects.append(Resto_coordinates(i))
    return map_objects


# creates data for the pie chart. lets a user review different stats for a single
# city at a time
#params: db_name, city, price_grp/rating_grp/review_grp/category
#returns: tuple
def create_donut_categories(db_name, city, var):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = ' SELECT ' + var
    q += ',count(*) as total '
    q += ' FROM Yelp_resto '
    q += ' WHERE City = ' + "'" + city + "'"
    q += ' GROUP BY  ' +  var

    cur.execute(q)
    yelp_tuple = cur.fetchall()
    return yelp_tuple

#creates input data for bars graph only selects city that
# were selected by user
#params: db_name
#returns: tuple
def create_bar_categories(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = '''
     SELECT distinct a.city, city_rate,  nation_rate, diff_rate
     FROM City_Obesity as a
     inner join Yelp_resto as  b on a.city = b.city
    '''
    cur.execute(q)
    yelp_tuple = cur.fetchall()
    return yelp_tuple


#creates input data for dot graph. select state from user and 5 above and 5 below
# based on an alphabetically sequenced list
#params: db_name, user selected state
#returns: tuple
def create_dot_categories(db_name, state):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = ' SELECT ID '
    q += ' FROM State_Obesity '
    q += ' WHERE State = ' + "'" + state + "'"
    q += ' LIMIT 10 '
    cur.execute(q)
    state_id = str(cur.fetchall()[0][0])

    q = ' SELECT * '
    q += ' FROM State_Obesity '
    q += ' WHERE ID >= '
    q += state_id
    q += ' - 5 and ID <= '
    q += state_id
    q += ' + 5'

    cur.execute(q)
    state_id = cur.fetchall()
    return state_id


# here is where the foreign key reference occurs
def create_table_categories(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    q = '''
     SELECT distinct a.city, a.state, d.category as top_food, city_rate, state_obesity_rate as state_rate, nation_rate
     FROM Yelp_resto as a
     INNER JOIN city_obesity as  b on a.city = b.city
     INNER JOIN state_obesity as c on a.state = c.state
     INNER JOIN (select city, category, count(category) as count_cat from Yelp_resto group by city, category) as d on a.city = d.city
     GROUP BY a.city, city_rate, state_obesity_rate, nation_rate
     HAVING max(count_cat)
    '''

    cur.execute(q)
    yelp_tuple = cur.fetchall()
    return yelp_tuple

# ######################
# Functions to graph user selections
# ######################

#map top 20 restaurants that a user selected
#params: db_name, city, and then can graph price, ratings, reviews, food
#returns: dot chart in plotly:
def map_resto (db_name, city):

    map_obj = create_map_list(db_name, city)

    lat_vals = []
    lon_vals = []
    text_vals = []
    for i in map_obj:
        try:
            lon_vals.append(i.long)
            lat_vals.append(i.lat)
            text_vals.append(i.name + " " + i.price)
        except:
            print("No location information")

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
                color ='red'
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
            title = "Top 20 Restaurants in " + city,
            geo = dict(
                scope='usa',
                projection=dict( type='albers usa' ),
                showland = True,
                showlakes = True,
                # landcolor = "rgb(250, 250, 250)",
                # subunitcolor = "rgb(100, 217, 217)",
                # countrycolor = "rgb(217, 100, 217)",
                lataxis = {'range': lat_axis},
                lonaxis = {'range': lon_axis},
                center= {'lat': center_lat, 'lon': center_lon },
                countrywidth = 3,
                subunitwidth = 3
            ),
        )


    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename='Top 20 restaurants' )


#produce a pie chart based on a city's restaurant features that a user choses.
#params: db_name, city, and then can graph price, ratings, reviews, food
#returns: dot chart in plotly:
def graph_donut(db_name, city, graph):
    donut_x = []
    donut_y = []

    if graph == "food":
        title = "Top 5 Food Categories"
        tuple_city = create_donut_categories(db_name = db_name, city = city , var =  'category')
        count = 1
        for i in tuple_city:
            donut_x.append(i[0])
            donut_y.append(i[1])
            if count == 5:
                break
            count+=1
    elif graph == "price":
        print(graph)
        title = "Restaurant Prices"
        tuple_city = create_donut_categories(db_name, city = city , var =  'price_grp')
        count = 1
        for i in tuple_city:
            donut_x.append(i[0])
            donut_y.append(i[1])
            if count == 5:
                break
            count+=1
    elif graph == "ratings":
        print(graph)
        title = "Restaurant Ratings"
        tuple_city = create_donut_categories(db_name = db_name, city = city , var =  'rating_grp')
        count = 1
        for i in tuple_city:
            donut_x.append(i[0])
            donut_y.append(i[1])
            if count == 5:
                break
            count+=1
    elif graph == "reviews":
        print(graph)
        title = "Restaurant Review Count"
        tuple_city = create_donut_categories(db_name = db_name, city = city , var =  'review_grp')
        count = 1
        for i in tuple_city:
            donut_x.append(i[0])
            donut_y.append(i[1])
            if count == 5:
                break
            count+=1

    fig = {
    "data": [
        {
          "values": donut_y,
          "labels": donut_x,
          "name": city,
          "hoverinfo":"label+percent+name",
          "hole": .4,
          "type": "pie"
        }
    ],

    "layout": {
        "title": title,
             "annotations": [
            {
                "font": {
                    "size": 20
                },
                "showarrow": False,
                "text":  city
            }
            ]
    }
    }
    py.plot(fig, filename='donut')

    print ("Check the interwebs for a donut :) ")

#produce a dot chart that shows the obesity rates across the nation, and broken down by gender
# a user choses a state, and then the functions chose the five preceding and five proceeding the state in
# an alphabetical lis
#params: db_name, state
#returns: dot chart in plotly
def graph_state_dot(db_name, state):
    overall = []
    men = []
    women = []
    states = []

    for i in create_dot_categories(db_name = db_name, state =  state):
        states.append(i[2])
        overall.append(i[3])
        men.append(i[4])
        women.append(i[5])

    trace1 = {"x": overall,
              "y": states,
              "marker": {"color": "yellow", "size": 12},
              "mode": "markers",
              "name": "Overall",
              "type": "scatter"
    }

    trace2 = {"x": men,
              "y": states,
              "marker": {"color": "blue", "size": 12},
              "mode": "markers",
              "name": "Men",
              "type": "scatter",
    }

    trace3 = {"x": women,
              "y": states,
              "marker": {"color": "pink", "size": 12},
              "mode": "markers",
              "name": "Women",
              "type": "scatter",
    }

    data = go.Data([trace1, trace2, trace3])
    layout = {"title": "Rate of Adult Obesity in " + state + " Compared to 10 Other States",
              "xaxis": {"title": "Crude Prevalence Rate", },
              "yaxis": {"title": "Alphabetical selection of closest ordered states to " +  state }}

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filenmae='basic_dot-plot')

    print("Check interwebs for dots :)")

#producing a bar chart that shows the difference between the obesity rate
# from cities selected by user that are in the 500 cities project compared to the
# average of all cities , e.g., national average
#params: db_name
#returns: bar chart on ploty
def graph_city_bar(db_name):
    city = []
    diff = []
    print(create_bar_categories)
    for i in create_bar_categories(db_name):

        city.append(i[0])
        diff.append(i[3])

    trace0 = go.Bar(
                x = city,
                y = diff
                )

    layout = go.Layout(
        title = "Adult prevalence for obesity in all selected cities <br> Difference calculated from average of all cities (national rate)",
        )

    data = go.Data([trace0])
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='basic-bar')

#produce a table of all cities key information that user selected from all three geographic levels
#params: db_name
#returns: table in plotly:
def graph_all_table(db_name):
    state  = []
    food   = []
    city   = []
    state  = []
    city_rate   = []
    state_rate  = []
    nation_rate = []
    for i in create_table_categories(db_name):
        city.append(i[0])
        state.append(i[1])
        food.append(i[2])
        city_rate.append(i[3])
        state_rate.append(i[4])
        nation_rate.append(i[5])
    trace = go.Table(
        header=dict(values=['City', 'State', 'Top Food', 'City Obesity Rate', 'State Obesity Rate', 'Nation Obesity Rate']),
        cells=dict(values=[city, state, food, city_rate, state_rate, nation_rate])
        )
    data = [trace]
    py.plot(data, filename = 'All Categories')
