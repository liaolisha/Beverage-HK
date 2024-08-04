import requests
import pandas as pd
import json
import psycopg2
import time
from datetime import datetime
# scraping data from HKTVmall, by requests.post(url,myobj)
# remember to change your connection in the data entry part
url = 'https://cate-search.hktvmall.com/query/products'

myobj = [] # collect the payload of the pages
for i in range(595): # this is the number of pages you want to scrape
    temp_dict = {
      'query': ':relevance:street:main:category:AA11220000000:',
      'currentPage': str(i), # this is the page number
      'pageSize': '60',
      'pageType': 'searchResult',
      'categoryCode': 'AA11220000000',
      'lang': 'zh',
      # CSRFToken must change
      'CSRFToken': '44e252d2-ac2b-4134-963d-36675ca00798'
    }
    myobj.append(temp_dict)
# create a list to store the json data after normalize
product_list = []

for y in range(595):
    try:
        x = requests.post(url, data = myobj[y]) # sending requests
        x_json = x.json()['products']
        x_json = pd.json_normalize(x_json)
        product_list.append(x_json)
    except Exception as e:
        print(f"error: {e},but we will continue to implement")
        continue
    
# Create a list to store extracted column data
extracted_list = []

# Iterate through the list and extract specific columns in each DataFrame
for i, df in enumerate(product_list):
    try:
        extracted_list.append(df[['code','name','url','averageRating','categories',
                              'numberOfReviews','brandName','packingSpec','countryOfOrigin',
                              'storeRating', 'storeName','storeType',
                              'price.value','savedPrice','salesVolume','storeCode',
                              'promotionText']])
    except KeyError as e:
        print(f"Some columns not found in {i}th DataFrame {e}")
        continue

# Use concat to merge all DataFrames into one
all_data = pd.concat(extracted_list)
# Transform data
# extract savedPrice.value from savePrice list, and remove '$', ',' and space
all_data['savedPrice.value'] = all_data['savedPrice'].apply(lambda x: float(x[0]['formattedValue'].replace("$", "").replace(",",'').strip())
                                                            if isinstance(x, list) and
                                                            len(x) > 0 and 'formattedValue'
                                                            in x[0] else 0)
# add 'scrap_date' column
from datetime import datetime
today = datetime.today().strftime('%Y-%m-%d')
all_data['scrap_date'] = today
# add current_price
all_data['current_price'] = all_data['price.value'] - all_data['savedPrice.value']
# extract category from categories, the category_list was scraped from HKTVmall - sub-category of non-alcoholic drinks
category_list = ['AA11220500001', 'AA11221000001', 'AA11221500001', 'AA11222000000', 'AA11222005001', 'AA11222010001',
                 'AA11222015001', 'AA11222500001', 'AA11223000001', 'AA11223500000', 'AA11223505001', 'AA11223510001',
                 'AA11224000000', 'AA11224005001', 'AA11224010001', 'AA11224015001', 'AA11224020001', 'AA11224025001',
                 'AA11224500000', 'AA11224505001', 'AA11224510001', 'AA11224515001', 'AA11225000000', 'AA11225005001',
                 'AA11225010001', 'AA11225015001', 'AA11225020001', 'AA11225025001', 'AA11225030001', 'AA11225500001']
all_data['categories'] = all_data['categories'].apply(lambda x: eval(str(x)))
def find_category(categories_list):
    for category_dict in categories_list:
        if category_dict['code'] in category_list:
            return category_dict['name']
    return None

all_data['category'] = all_data['categories'].apply(find_category)
current_date = datetime.today().date().strftime('%Y-%m-%d')
# Export to Excel file
name = current_date + '_Hktvmall.xlsx'
all_data.to_excel(name, index=False)

df = pd.read_excel(name)
df['scrap_date'] = pd.to_datetime(current_date)
df = df.drop_duplicates(subset=['code', 'storeCode'], keep='first')

# change your connection details here

conn = psycopg2.connect(
    host = "localhost",
    dbname = "", 
    user = "postgres",
    password = "",
    port = 5432
)
cur = conn.cursor()

product_id = df["code"].tolist()
product_name = df["name"].tolist()
brand_name = df["brandName"].tolist()
packing = df["packingSpec"].tolist()
country = df["countryOfOrigin"].tolist()
category = df["category"].tolist()

products_hktv_dict_list = []
for a, b, c, d, e, f in zip(product_id, product_name, brand_name, packing, country, category):
    product = { 'product_id': a, 'product_name': b, 'brand_name': c, 'packing': d, 'country': e, 'category': f}
    products_hktv_dict_list.append(product)

insert_query = """INSERT INTO products_HKTV (product_name, brand_name, product_id, packing, country, category)
VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (product_id) 
DO NOTHING"""

cur.executemany(insert_query, [(d["product_name"], d["brand_name"], d["product_id"], d["packing"], d["country"], d['category']) for d in products_hktv_dict_list])

store_id = df["storeCode"].tolist()
store_name = df["storeName"].tolist()
store_rating = df["storeRating"].tolist()

store_hktv_dict_list = []
for a, b, c in zip(store_id, store_name, store_rating):
    product = { 'store_id': a, 'store_name': b, 'store_rating': c}
    store_hktv_dict_list.append(product)

insert_query = """
    INSERT INTO store_HKTV (store_id, store_name, store_rating) 
    VALUES (%s, %s, %s) 
    ON CONFLICT (store_id) 
    DO NOTHING
"""
cur.executemany(insert_query, [(d["store_id"], d["store_name"], d["store_rating"]) for d in store_hktv_dict_list])

product_id = df["code"].tolist()
unit_price = df["price.value"].tolist()
current_price = df["current_price"].tolist()
promotion_text = df["promotionText"].tolist()
rating = df["storeRating"].tolist()
no_of_reviews = df["numberOfReviews"].tolist()
quantity = df["salesVolume"].tolist()
scrap_date = df["scrap_date"].tolist()

fact1_hktv_dict_list = []
for a, b, c, d, e, f, g, h in zip(product_id, unit_price, current_price, promotion_text, rating, no_of_reviews, quantity, scrap_date):
    product = { 'product_id': a, 'unit_price': b, 'current_price': c, 'promotion_text': d, 'rating': e, 'no_of_reviews': f, 'quantity': g, 'scrap_date': h}
    fact1_hktv_dict_list.append(product)

insert_query = """
    INSERT INTO fact_HKTV (product_id, unit_price, current_price, promotion_text, rating, no_of_reviews, quantity, scrap_date) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)  ON CONFLICT (product_id, scrap_date) 
    DO NOTHING

"""
cur.executemany(insert_query, [(d["product_id"], d["unit_price"], d["current_price"], d["promotion_text"], d["rating"], d["no_of_reviews"], d['quantity'], d['scrap_date']) for d in fact1_hktv_dict_list])

product_id = df["code"].tolist()
store_id = df["storeCode"].tolist()

store23_hktv_dict_list = []
for a, b in zip(product_id, store_id):
    product = {'product_id': a, 'store_id': b}
    store23_hktv_dict_list.append(product)

insert_query = """
    INSERT INTO product_store_HKTV (product_id, store_id) 
    VALUES (%s, %s)  ON CONFLICT (product_id, store_id) 
    DO NOTHING

"""
cur.executemany(insert_query, [(d["product_id"], d["store_id"]) for d in store23_hktv_dict_list])

conn.commit()

# 关闭游标和数据库连接
cur.close()
conn.close()
    


