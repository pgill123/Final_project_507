from  final_project_507 import *
db_name = city_db

# print_db_contents(city_db)
# print_table_all(db_name, "Yelp_resto")
# print_table_contents(db_name, "Yelp_resto")
# print_table_all(db_name, "State_obesity")
# print_table_all(db_name, "City_obesity")

# # ######################
# # Call functions to create data
# # ######################

check_csv_exists(city_db)

keep_loop = "yes"
while keep_loop.strip().lower() == "yes":
    user_city = input("(1) What city would like to see restaurant and health results displayed for? Enter city and state, separated by a comma. ")
    #check here if the city is in the 500 cities database. If not, suggest a different city.

    city = user_city.strip().split(",")[0]
    state = user_city.strip().split(",")[1]

    # verify city exists in 500 cities project
    city_in_db = check_city_exists(city_db, city)

    if city_in_db == True:
        insert_json(db_name, city, state)
        mod_yelp(db_name)
        yelp_resto_update = check_yelp_table(db_name, city)
        print(yelp_resto_update)
        yelp_add(db_name,yelp_resto_update )
        # print_table_all(db_name, "Yelp_resto")

        keep_graph = "yes"
        while keep_graph.strip().lower() == "yes":
            user_graph = input("(2) What information would you like to see? Refer to README for commands. ")
            user_graph_list = user_graph.strip().split(", ")
            len_graph_list = len(user_graph_list)

            donut_choice = ["food", "price", "ratings", "reviews"]

            try:
                if "map" in user_graph_list:
                    print("See plotly for a map of top 20 restaurants and their costs.")
                    map_resto(db_name, user_graph_list[1])
                if "table" in user_graph_list:
                    print("See plotly for a table of key information for all cities in Yelp db.")
                    graph_all_table(db_name)
                if "graph" in user_graph_list:
                    if len_graph_list == 3:
                        if user_graph_list[2] in donut_choice:
                            graph_donut(db_name, user_graph_list[1], user_graph_list[2])
                        else:
                            print("Incorrect choice. Refer to README.")
                    elif len(user_graph_list) == 2:
                        print("See plotly for a graph of obesity rates for state and comparison states, broken down overall and by gender.")
                        graph_state_dot(db_name, user_graph_list[1])
                    elif len(user_graph_list) == 1:
                        print("See plotly for a graph of obesity rate differences for all cities in Yelp database.")
                        graph_city_bar(db_name)
                    else:
                        print("Incorrect choice. Refer to README.")
            except:
                print("Incorrect command. Try again.")

            keep_graph = input("Do you want to plot another graph? (Enter 'yes' to continue.)")

    else:
        print(city  + " is not in the 500 cities project data base. Try another (bigger?) city.")

    keep_loop = input("Do you want to view another city? (Enter 'yes' to continue.)")

print("Thanks, bye!")

# ######################
# Call functions to create graphs
# ######################
# insert_csv('city_food.db')
# mod_city('city_food.db')
# mod_state('city_food.db')
# user_graph_list = ['graph,', 'Cleveland,', 'food']
# graph_donut(db_name  = db_name, city = user_graph_list[1] , graph = user_graph_list[2] )
#
# graph_donut(db_name  = db_name, city = 'Cleveland' , graph = 'food' )

# insert_json('city_food.db', 'Cleveland', 'OH')
# insert_json('city_food.db', 'Ann Arbor', 'MI')
# insert_json('city_food.db', 'New York', 'New York')
# insert_json('city_food.db', 'Miami', 'FL')
# mod_yelp('city_food.db')
# yelp_add('city_food.db', "add")
# print_db_contents('city_food.db')
# table = 'Yelp_resto'
# city_db = 'city_food.db'
# city = "Miami"
# print_table_all(db_name, "Yelp_resto")
# map_resto(city_db, city)
# graph_donut(db_name  = 'city_food.db', city = city , graph = "food" )
# graph_city_bar(db_name  = 'city_food.db')
# graph_state_dot(db_name = 'city_food.db', state = 'MI')
# graph_all_table(db_name = 'city_food.db')
