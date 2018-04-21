import unittest
from final_project_507 import *
db_name = 'city_food.db'

# NOTE: Unit tests require running Cleveland first and Denver second


class TestDatabase(unittest.TestCase):
    # verify records are being added (number and city)
    #verify data processing work
    def test_yelp(self):
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        #verify correct number of records pull and get entered to db
        q = ' SELECT count(*) '
        q += ' FROM Yelp_resto '
        q += ' WHERE City = "Cleveland"'

        cur.execute(q)
        count_yelp = cur.fetchone()
        # print("count_yelp", count_yelp[0])

        # verify only unique cities get entered (if add city more than once, not renter records)
        q = ' SELECT City, count(*)'
        q += ' FROM Yelp_resto '
        q += ' GROUP BY city '
        q += ' HAVING count(*) > 50'

        cur.execute(q)
        multi_entry_tuple = cur.fetchone()
        # print("multi_entry_tuple",multi_entry_tuple)


        # verify processing worked
        q = ' SELECT name, price, price_grp, rating, rating_grp '
        q += ' FROM Yelp_resto '
        q += ' WHERE City = "Cleveland"'

        cur.execute(q)
        processing_tuple = cur.fetchall()
        # print("processing_tuple", processing_tuple[0][0], processing_tuple[1][4], processing_tuple[4][2])

        self.assertEqual(count_yelp[0], 50)
        self.assertEqual(multi_entry_tuple, None)
        self.assertTrue(processing_tuple[0][0] == 'Lola')
        self.assertTrue(processing_tuple[1][4] == '3 star')
        self.assertTrue(processing_tuple[4][2] == 'Medium')


    def test_cdc(self):
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()

        # verify only 54 states and terriroties (PR, GU, DC, VI)
        q = ' SELECT count(*)'
        q += ' FROM State_obesity '

        cur.execute(q)
        count_state = cur.fetchone()
        # print("count_state", count_state[0])

        # verify only 500 cities
        q = ' SELECT count(*)'
        q += ' FROM City_obesity '
        q += ' WHERE state <> "US" '

        cur.execute(q)
        count_city = cur.fetchone()
        # print("count_city", count_city[0])

        # verify difference calculation
        q = ' SELECT * '
        q += ' FROM city_obesity '
        cur.execute(q)
        check_city_processing = cur.fetchone()

        self.assertEqual(count_state[0], 54)
        self.assertEqual(count_city[0], 500)
        self.assertGreater(check_city_processing[5], check_city_processing[6])
        self.assertEqual(check_city_processing[6], -2.9)

    def test_graph_data(self):
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()

        #verify donut categories
        q = ' SELECT category '
        q += ',count(*) as total '
        q += ' FROM Yelp_resto '
        q += ' WHERE City = "Cleveland" '
        q += ' GROUP BY  category '
        cur.execute(q)
        check_donut = cur.fetchone()
        use_donut = create_donut_categories(db_name, "Cleveland", "category")

        #pull a middle state and verify 11 records are pulled
        check_dot = len(create_dot_categories(db_name, "OH"))

        #check table craetion
        q = ' SELECT count(distinct city) '
        q += ' FROM Yelp_resto '
        cur.execute(q)
        check_table = cur.fetchone()[0]
        use_table = len(create_table_categories(db_name))

        self.assertEqual(check_donut[0], use_donut[0][0])
        self.assertEqual(check_dot, 11)
        self.assertEqual(check_table, use_table)


    def test_graph(self):
        try:
            graph_city_bar(db_name)
        except:
            self.fail()

        try:
            graph_state_dot(db_name, "OH")
        except:
            self.fail()

            try:
                graph_state_dot(db_name, "OH")
            except:
                self.fail()

        try:
            map_resto(db_name, "Denver")
        except:
            self.fail()

unittest.main(verbosity=2)
