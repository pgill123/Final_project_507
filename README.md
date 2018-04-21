# Final_project_507

I have a professional interest in health and poverty and a personal interest in food cultures. 
My project combines these interests by searching Yelp for top 50 restaurants in a city of the user’s 
selection and then returns to the user graphical displays that showcase restaurants, food preferences 
and pricing, and adult obesity at the city, state and national levels using data from the CDC. 
Information is accumulated as a user select more cities to allow for comparisons. Graphs and tables are displayed using Plotly. 
Only cities in the 500 Cities Project by the CDC are eligible for consideration so that comparison can be made.


See help.txt for how to run the program and visualize the data. Below is information on the program structure.

STEPS TO RUN 
Download two csv files. Verify files names in the program header of final_project_507.py. Retrieve an API Key from Yelp Fusion. Enter credentials into the starter file yelp_secret.py

DATABASE
Databased created called 'city_db' that has six different tables. 

Yelp_raw: 
Primary key: Restaurant, Foreign Keys: City, State
The Yelp API is used to get a top 50 set of restaurants based on a user's selection for a city. Restaurants are selected based on highest review count, indicating popularity. Information on price, ratings, reviews, food category, and location are stored and manipulated later. To ensure restaurants located outside of the immediate city boundaries are still grouped with the user selected city for aggregation, the city field in this data set is programmatically entered.
Requirements: User API Key required. Place in yelp_secret.py file. https://www.yelp.com/developers/documentation/v3/authentication#where-is-my-client-secret-going 

City_raw:
Primary Key: City, State 
A CSV file that shows data from the 500 Cities Project. The project is run by the CDC and it combines local data received from city health departments to report on a number of key health issues and the crude prevalence ratio (i.e., the percentage of residents exhibiting that health conditions based on the total number of residents). 
Requirements: Download csv file https://catalog.data.gov/dataset/500-cities-local-data-for-better-health-b32fd

State_raw: 
Primary Key: State 
A CSV file from the CDC displaying for chronic disease indicators (CDI) in all 50 states. CDIs enables public health professionals and policymakers to retrieve uniformly defined state level data for chronic diseases and risk factors that have a substantial impact on public health. It also stores the rates by different subgroups. The file structured in a long format with repeated records for various measures and subgroups.
Requirements: Download csv file https://catalog.data.gov/dataset/u-s-chronic-disease-indicators-cdi

Yelp_restos: (used in graphs)
Primary key: Restaurants
This data set accumulates user's selections from Yelp_raw and manipulates variables to create the following for graphical presentation
	Price_grp: 1,2 = Low; 3 = Medium; 4,5 = High 
	Review count: 0- 199, 200 to 599, 600 to 999, 1000+
	Rating: 1 star, 2 star, 3 star, 4 star, 5 star

City_Obesity: (used in graphs)
Data used subsetted from City_raw to only include to adult onset of obesity prevalence ratios (e.g., obesity among adults aged >= 18 years).
	City_rate: Crude prevalence for city 
	Nation_rate: Crude prevalence among all 500 cities
	Diff_rate: Difference between the city and nation rate, which will be plotted

State_Obesity: (used in graphs)
Data are subsetted from State_raw to only include adult obesity are for the state, and also, for women and men in the state to review obesity rates by a gender subgroup. 54 states and territories are included but the Virgin Islands (VI) have no data on obesity. 
	State_obesity_rate: Obesity among adults aged >= 18 years
	State_men_obesity_rate: Obesity among adults aged >= 18 years
	State_women_obesity_rate: Obesity among adults aged >= 18 years

PROGRAMS
final_project_507.py 
	stores all functions used in the programs. verify uploaded csv files names match what is program header. 
user_calls.py 
	use this program to interactively run all functions and plots
final_project_507_test.py 
	use this program to run all unit tests to verify program and data created\
	for unit tests to work, must have first entered Cleveland into the db, and then Denver
yelp_secret.py
	place api key for yelp here

CODE 
The code reads in data to create three raw tables, process it to create three modified tables,
manipulates the modified data to create tuples that cut the data in different ways for display, 
and then finally graphs the data. Lesser functions include those for checking in data files exists
or if certain user calls are valid. 

Key functions used are:
mod_yelp 
	modifies Yelp_raw usingcase when statements
yelp_add 
	adds the modified Yelp_raw to a new table, Yelp_restos. This table accumulates 
	until the user choses to start over. 
mod_city 
	modifies City_raw using inner querry to aggregate data
mod_state 
	modifies State_raw using aggregate functions to convert a long table into a wide table
create_table_categories
	merges together all data using primary and foreign keys to create a summary table
create_map_list
	uses the class Restos_coordinates to generate information for plotting a map

