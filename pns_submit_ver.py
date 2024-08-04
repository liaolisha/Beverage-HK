
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import numpy as np
import multiprocessing
import pandas as pd
from datetime import datetime
import time
import re
import os
# remember to change your connection in the data entry part

driver = webdriver.Chrome()
url = "https://www.pns.hk/zh-hk/%E9%A3%B2%E5%93%81%E3%80%81%E5%8D%B3%E6%B2%96%E9%A3%B2%E5%93%81/lc/04010000"
driver.get(url)
time.sleep(8)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight/10);")
time.sleep(2)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight/20);")
try:
    show_all_btn = driver.find_element(By.CSS_SELECTOR, 'div.toggleAllBtn')
    show_all_btn.click()
    time.sleep(2)
except Exception:
    pass
all_links = []
no_swiper_div = driver.find_element(By.CSS_SELECTOR, '.no-swiper')
links = no_swiper_div.find_elements(By.TAG_NAME, 'a')
for link in links:
    if link.get_attribute("href") != None:
        all_links.append(link.get_attribute("href"))
filtered_links = [link.get_attribute("href") for link in links if '酒精飲品' not in link.text] # as all_links[1:]

def scrape_products(max_products):
    for n in range(1, max_products + 1):

        brand_list = f"brand_list{n}"
        pd_name_list = f"pd_name_list{n}"
        List_all = f"List_all{n}"
        each_product_url_list = f"each_product_url_list{n}"

        globals()[brand_list] = []
        globals()[pd_name_list] = []
        globals()[List_all] = []
        globals()[each_product_url_list] = []

        driver.get(f'{filtered_links[n-1]}')
        time.sleep(1)
        if n>8:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/10);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/10);")
            time.sleep(1)
            product_quantity_element = driver.find_elements(By.CSS_SELECTOR, ".product-quantity")
        else:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/20);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/20);")
            time.sleep(2)
            product_quantity_element = driver.find_elements(By.CSS_SELECTOR, ".product-quantity")

        for nums in product_quantity_element:
            num = nums.text
            num_only = re.search(r'\d+', num)
            num_only = int(num_only.group())
            time.sleep(2)
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".productContainer")))
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scroll_count = int(num_only / 15) - 1

            while scroll_count < max_scroll_count:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_count += 1
                else:
                    scroll_count = 0
                last_height = new_height

            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "productName")))
            product_group = driver.find_elements(By.CLASS_NAME, "productName")

            for result_compo in product_group:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-group")))

                lines = result_compo.text.split('\n')
                globals()[brand_list].append(lines[0])
                globals()[pd_name_list].append(lines[1])
                globals()[each_product_url_list].append(result_compo.get_attribute('href'))
                globals()[List_all].append({
                    'brand': lines[0],
                    'product_name': lines[1],
                    'product_url': result_compo.get_attribute('href')
                })

scrape_products(10) #len(filtered_links)

def process_range(start, end):
    # Create a new WebDriver instance for each process
    driver = webdriver.Chrome()

    for n in range(start, end):
        pd_info_full_list = f"pd_info_full_list{n}"
        each_product_url_list = f"each_product_url_list{n}"
        globals()[pd_info_full_list] = []
        missing_indices = []

        for i in range(0, len(globals()[each_product_url_list])):
            try:
                driver.get(f'{globals()[each_product_url_list][i]}')
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info-group')))

                max_retries = 5
                retries = 0
                product_info = None
                while retries < max_retries:
                    try:
                        product_info = driver.find_elements(By.CSS_SELECTOR, '.product-info-group')
                        break
                    except StaleElementReferenceException:
                        retries += 1
                        print(f"StaleElementReferenceException occurred for URL: {globals()[each_product_url_list][i]}. Retrying... (Attempt {retries}/{max_retries})")
                        if retries == max_retries:
                            missing_indices.append(i)
                            globals()[pd_info_full_list].append('N/A')

                if product_info:
                    for info in product_info:
                        try:
                            product_content = info.text.split('\n')
                            globals()[pd_info_full_list].append(product_content)
                            print(product_content)
                        except StaleElementReferenceException:
                            print(f"StaleElementReferenceException occurred while processing product information for URL: {globals()[each_product_url_list][i]}")
                            globals()[pd_info_full_list].append('N/A')
                            missing_indices.append(i)
                            continue
                else:
                    print(f"Unable to find product information for URL: {globals()[each_product_url_list][i]}")
                    globals()[pd_info_full_list].append('N/A')
                    missing_indices.append(i)

            except TimeoutException:
                print(f"TimeoutException occurred for URL: {globals()[each_product_url_list][i]}")
                globals()[pd_info_full_list].append('N/A')
                missing_indices.append(i)
                continue

        # Retry the missing indices
        for index in sorted(missing_indices, reverse=True):
            try:
                driver.get(f'{globals()[each_product_url_list][index]}')
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info-group')))
                product_info = driver.find_elements(By.CSS_SELECTOR, '.product-info-group')
                if product_info:
                    for info in product_info:
                        try:
                            product_content = info.text.split('\n')
                            globals()[pd_info_full_list][index] = product_content
                            print(product_content)
                        except StaleElementReferenceException:
                            print(f"StaleElementReferenceException occurred while processing product information for URL: {globals()[each_product_url_list][index]}")
                            continue
            except (TimeoutException, StaleElementReferenceException):
                print(f"Error occurred while retrying URL: {globals()[each_product_url_list][index]}")
                continue
    print(missing_indices) #add to show any missing
    # Close the WebDriver instance
    driver.quit()

if __name__ == "__main__":
    # Create and start the processes
    process1 = multiprocessing.Process(target=process_range, args=(1, 5,))
    process2 = multiprocessing.Process(target=process_range, args=(5, 8,))
    process3 = multiprocessing.Process(target=process_range, args=(8, 11,))

    process1.start()
    process2.start()
    process3.start()

    # Wait for the processes to finish
    process1.join()
    process2.join()
    process3.join()

# range_no=len(filtered_links)+1 as 11
process_range(1, 11)

c1_brand_name_list = brand_list1
c1_product_name_list = pd_name_list1

def process_data(c_brand_name_list, c_product_name_list, pd_info_full_list):
    c_sales_amount_list = []
    c_rating_list = []
    c_comment_list = []
    c_packing_list = []
    c_current_price_list = []
    c_original_price_list = []
    c_stock_stage_list = []
    c_origin_list = []
    c_discount_list = []

    for product_name, brand_name in zip(c_product_name_list, c_brand_name_list):
        found = False
        for item in pd_info_full_list:
            if product_name == item[2] and brand_name == item[1]:
                found = True
                try:
                    c_sales_amount_list.append((next(x for x in item if '已售' in x))[3:])
                except StopIteration:
                    c_sales_amount_list.append('N/A')

                try:
                    c_rating_list.append(next(f"{x/10:.1f}" for x in range(0, 51, 1) if f"{x/10:.1f}" in item))
                except StopIteration:
                    c_rating_list.append('N/A')

                try:
                    c_comment_list.append(next(x for x in item if '評價' in x))
                except StopIteration:
                    c_comment_list.append('N/A')

                try:
                    comment_item = next(x for x in item if '評價' in x)
                    packing_start_index = item.index(comment_item) + 1
                    c_packing_list.append(next((x for x in item[packing_start_index:] if '$' not in x), 'N/A'))
                except (StopIteration, ValueError):
                    c_packing_list.append('N/A')

                try:
                    # Extract current price
                    current_price_pattern = r'\$(\d+(?:\.\d+)?)'
                    current_price_match = re.search(current_price_pattern, str(item))
                    if current_price_match:
                        c_current_price_list.append(current_price_match.group(1))
                    else:
                        c_current_price_list.append('N/A')

                    # Extract original price
                    original_price_pattern = r'\$(\d+(?:\.\d+)?)'
                    original_price_match = re.search(original_price_pattern, str(item))
                    if original_price_match:
                        c_original_price_list.append(original_price_match.group(1))
                    else:
                        c_original_price_list.append('N/A')
                except:
                    c_current_price_list.append('N/A')
                    c_original_price_list.append('N/A')
                try:
                    has_dollar = False
                    stock_stage = 'N/A'
                    for j, x in enumerate(item):
                        if '$' in x:
                            has_dollar = True
                        elif has_dollar and '有貨'or '加入購物車'or'加入我的購物清單'or'少量存貨' in x:
                            stock_stage = True
                            break
                    c_stock_stage_list.append(stock_stage)
                except:
                    c_stock_stage_list.append(False)

                try:
                    has_dollar = False
                    discount_info = ''
                    for j, x in enumerate(item):
                        if '$' in x:
                            has_dollar = True
                            current_price_index = j
                        elif has_dollar and '買' in x:
                            discount_info = x
                            if j + 1 < len(item) and '$' in item[j+1]:
                                discount_info += item[j+1]
                            if j + 2 < len(item) and '/件' in item[j+2]:
                                discount_info += item[j+2]
                            c_discount_list.append(True)
                            break
                    if not discount_info:
                        c_discount_list.append(False)
                except:
                    c_discount_list.append(False)
                try:
                    origin_index = next((j for j, x in enumerate(item) if '原產地' in x), -1)
                    if origin_index != -1:
                        c_origin_list.append(item[origin_index + 1])
                    else:
                        c_origin_list.append('N/A')
                except:
                    c_origin_list.append('N/A')

                found = True
                break

        if not found:
            c_sales_amount_list.append(' ')
            c_rating_list.append(' ')
            c_comment_list.append(' ')
            c_packing_list.append(' ')
            c_current_price_list.append('N/A')
            c_original_price_list.append('N/A')
            c_stock_stage_list.append(' ')
            c_origin_list.append(' ')
            c_discount_list.append(' ')

    # craete dict
    data_dict = {
        'brand_name': c_brand_name_list,
        'product_name': c_product_name_list,
        'quantity': c_sales_amount_list,
        'rating': c_rating_list,
        'no_of_reviews': c_comment_list,
        'packing': c_packing_list,
        'current_price': c_current_price_list,
        'unit_price': c_original_price_list,
        'stock_status': c_stock_stage_list,
        'country': c_origin_list,
        'promotion_status': c_discount_list
    }

    # Create DataFrame
    df = pd.DataFrame(data_dict)

    return df

all_data = pd.DataFrame()
for dataset_num in range(1, 11): #As ttl 10 set
    c_brand_name_list = eval(f"brand_list{dataset_num}")
    c_product_name_list = eval(f"pd_name_list{dataset_num}")
    pd_info_full_list = eval(f"pd_info_full_list{dataset_num}")

    df = process_data(c_brand_name_list, c_product_name_list, pd_info_full_list)

    if dataset_num == 1:
        df['category'] = '水 蒸餾水, 礦泉水'
    elif dataset_num == 2:
        df['category'] = '汽水'
    elif dataset_num == 3:
        df['category'] = '即飲茶類、咖啡、奶茶'
    elif dataset_num == 4:
        df['category'] = '奶類、乳酪飲品'
    elif dataset_num == 5:
        df['category'] = '植物奶、大豆飲品'
    elif dataset_num == 6:
        df['category'] = '咖啡、沖調飲品、熱飲'
    elif dataset_num == 7:
        df['category'] = '果汁、椰子水'
    elif dataset_num == 8:
        df['category'] = '運動及能量飲品'
    elif dataset_num == 9:
        df['category'] = '草本及健康飲品'
    elif dataset_num == 10:
        df['category'] = '原箱飲品'

    all_data = pd.concat([all_data, df], ignore_index=True)

# 保存 all_data as CSV file
def convert_quantity(x):
    if isinstance(x, str):
        if 'K' in x:
            return int(float(x.replace('K', '').replace('+', '')) * 1000)
        elif 'M' in x:
            return int(float(x.replace('M', '').replace('+', '')) * 1000000)
        elif '+' in x:
            return int(float(x.replace('+', '')))
        elif x == '':
            return 0
        elif x.strip() == '':
            return 0
        elif x.lower() == 'n/a':
            return 0
        else:
            return int(x)
    else:
        return x

current_date = datetime.now().strftime('%Y-%m-%d')

all_data['quantity'] = all_data['quantity'].apply(convert_quantity)

all_data['no_of_reviews'] = all_data['no_of_reviews'].astype(str)
all_data['no_of_reviews'] = all_data['no_of_reviews'].str.extract(r'(\d+)', expand=False)
all_data['no_of_reviews'] = all_data['no_of_reviews'].fillna(0).astype(int)

all_data['rating'] = all_data['rating'].replace(' ', np.nan)
all_data['rating'] = all_data['rating'].replace('N/A', np.nan)
all_data['rating'] = all_data['rating'].fillna(0)
all_data['rating'] = all_data['rating'].astype(float)
#all_data['no_of_reviews'] = all_data['no_of_reviews'].fillna(0)
#all_data['no_of_reviews'] = all_data['no_of_reviews'].astype(int)
all_data['unit_price'] = all_data['unit_price'].astype(str)
all_data['current_price'] = all_data['current_price'].astype(str)
all_data['unit_price'] = all_data['unit_price'].str.replace('$', '')
all_data['current_price'] = all_data['current_price'].str.replace('$', '')
all_data['unit_price'] = all_data['unit_price'].replace('N/A', '0').astype(float)
all_data['current_price'] = all_data['current_price'].replace('N/A', '0').astype(float)

all_data['promotion_status'] = all_data['promotion_status'].astype(bool)
all_data['stock_status'] = all_data['stock_status'].astype(bool)
all_data['scrap_date'] = current_date
all_data['scrap_date'] = pd.to_datetime(all_data['scrap_date'])
all_data = all_data.replace('N/A', None)
all_data.loc[all_data['unit_price'] == 0, 'unit_price'] = all_data['current_price'] #new add

price_diff = all_data['current_price'] - all_data['unit_price']#new add
mask = price_diff.gt(0)#new add
result = all_data[mask] #new add
# updat 'unit_price' as 'current_price' 's value (if unit_price value --> from discount place, that lower than current_price)
if not result.empty:#new add
    all_data.loc[mask, 'unit_price'] = all_data.loc[mask, 'current_price']#new add

filename = f'pns_all_category_{current_date}.csv'

csv_dir = r"C:\Users\yim\Desktop\VS_JDE_10\classes\csv file"
if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

filename = os.path.join(csv_dir, f'pns_all_category_{current_date}.csv')
all_data.to_csv(filename, index=False)


import pandas as pd

#step 1 import file


from datetime import datetime
current_date = datetime.now().strftime('%Y-%m-%d')
filename = f'pns_all_category_{current_date}.csv'

while True:
    try:
        df = pd.read_csv(filename)
        break
    except FileNotFoundError:
        print("File not found. Please try again.")
    except pd.errors.EmptyDataError:
        print("File is empty. Please try again.")
    except pd.errors.ParserError:
        print("Error parsing file. Please try again.")


df = df.drop_duplicates(subset=['brand_name', 'packing', 'product_name'],keep='first')


df['current_price'] = df['current_price'].replace(' ', None)
df['unit_price'] = df['unit_price'].replace(' ', None)
df['country'] = df['country'].replace(' ', None)
df['country'] = df['country'].replace('NaN', None)
df['quantity'] = df['quantity'].replace('N/A', None)
df['packing'] = df['packing'].replace(' ', 'NaN')
df['quantity'] = df['quantity'].replace(' ', None)



# handling country col 
country = df["country"].to_list()
new_country = []

for i in country:
    if i == "UK":
        new_country.append("英國")
        print("1")
    elif i == "中國內地":
        new_country.append("中國")
        print("2")
    elif i == "新西蘭<BR>":
        new_country.append("新西蘭")
        print("3")
    elif i == "原產地: 中國<BR>台灣包裝":
        new_country.append("中國")
        print("4")
    elif i == "斯里蘭卡<BR>":
        new_country.append("斯里蘭卡")
        print("5")
    elif i == "中國 (香港調配)":
        new_country.append("中國")
        print("6")
    elif i == "馬來西亞︰清涼爽, 菊花茶, 甘蔗水<br/><br/>中國︰馬蹄爽":
        new_country.append("馬來西亞, 中國")
        print("7")
    elif i == "中國<br/>(香港調配)<br/>":
        new_country.append("中國")
        print("8")
    elif i == 'NaN':
        new_country.append(None)
        print("9")
    else:
        new_country.append(i)     

df = df.assign(country=new_country)

import re

def format_volume_list(volume_list):
    formatted_list = []

    for volume in volume_list:
        if volume is None:  
            formatted_list.append(None)
            continue
        
        # Ensure that the volume is a string before matching
        match = re.match(r"(\d+(\.\d+)?)(L|ML)(x(\d+))?", str(volume), re.IGNORECASE)
        if match:
            size, unit, multiplier = match.group(1), match.group(3).upper(), match.group(5)
            size = float(size) * (1000 if unit == "L" else 1)  
            count = int(multiplier) if multiplier else 1
            formatted_list.append(f"{count}x{int(size)}ML")
        else:
            formatted_list.append(volume)  

    return formatted_list


packing = df["packing"].to_list()
print(packing)
new_packing = format_volume_list(packing)
print(new_packing)
# replace it with new_country
df = df.assign(packing=new_packing)

stock_status = df["stock_status"].tolist()
new_stock_status = []
for i in stock_status:
    if type(i) != bool:
        new_stock_status.append(None)
    else:
        new_stock_status.append(i)
df = df.assign(stock_status=new_stock_status)

df.to_csv(f'pns_all_category_cleaned_{current_date}.csv') 

import psycopg2
import pandas as pd
# change your connection details here

conn = psycopg2.connect(
    host = "localhost",
    dbname = "", 
    user = "postgres",
    password = "",
    port = 5432)

cur = conn.cursor()

import datetime

current_date = datetime.now().strftime('%Y-%m-%d')
filename = f'pns_all_category_cleaned_{current_date}.csv'
df = pd.read_csv(file_name)

cur.execute("""
    CREATE TABLE IF NOT EXISTS fact_pns (
        product_name VARCHAR(255),
        brand_name VARCHAR(255),
        packing VARCHAR(50),
        scrap_date TIMESTAMP,
        quantity DOUBLE PRECISION,
        current_price DOUBLE PRECISION,
        unit_price DOUBLE PRECISION,
        stock_status BOOLEAN,
        rating DOUBLE PRECISION,
        no_of_reviews INT,
        promotion_status BOOLEAN,
        PRIMARY KEY(product_name, packing, brand_name , scrap_date)
    )
""")
conn.commit()

fact_pns = pd.read_csv(file_name) #change

product_name = fact_pns["product_name"].tolist()
brand_name = fact_pns["brand_name"].tolist()
packing = fact_pns["packing"].tolist()
scrap_date = fact_pns["scrap_date"].tolist()
quantity = fact_pns["quantity"].tolist()
current_price = fact_pns["current_price"].tolist()
unit_price = fact_pns["unit_price"].tolist()
stock_status = fact_pns["stock_status"].tolist()
rating = fact_pns["rating"].tolist()
no_of_reviews = fact_pns["no_of_reviews"].tolist()
promotion_status = fact_pns["promotion_status"].tolist()

fact_pns_dict_list = []
for a, b, c, d, e, f,g,h,i, j,k in zip(product_name,brand_name , packing, scrap_date, quantity, current_price, unit_price, stock_status, rating, no_of_reviews, promotion_status):
    product = { 'product_name': a, 'brand_name': b, 'packing': c, 'scrap_date': d, 'quantity': e, 'current_price': f, 'unit_price': g, 'stock_status': h, 'rating': i, 'no_of_reviews': j, 'promotion_status': k  }
    fact_pns_dict_list.append(product)
    
print(len(fact_pns_dict_list))

insert_query = """INSERT INTO fact_pns (product_name, brand_name, packing, scrap_date, quantity, current_price, unit_price, stock_status, rating, no_of_reviews, promotion_status)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

cur.executemany(insert_query, [(d["product_name"], d["brand_name"], d["packing"], d["scrap_date"], d["quantity"], d["current_price"], d["unit_price"], d["stock_status"], d["rating"], d["no_of_reviews"], d["promotion_status"]) for d in fact_pns_dict_list])

#conn.commit()

#for the first time
cur.execute("""
    CREATE TABLE IF NOT EXISTS product_pns (
        product_name VARCHAR(255),
        brand_name VARCHAR(255),
        category VARCHAR(255),
        packing VARCHAR(50),
        country VARCHAR(255),
        primary key(product_name, brand_name, packing)
    )
""")

conn.commit()

product_pns = pd.read_csv(file_name)

product_name = product_pns["product_name"].tolist()
brand_name = product_pns["brand_name"].tolist()
category = product_pns["category"].tolist()
packing = product_pns["packing"].tolist()
country = product_pns["country"].tolist()

product_pns_dict_list = []
for a, b, c, d, e,  in zip(product_name, brand_name, category, packing, country):
    product = { 'product_name': a, 'brand_name': b, 'category': c, 'packing': d, 'country': e  }
    product_pns_dict_list.append(product)
print(len(product_pns_dict_list))


insert_query = """INSERT INTO fact_pns (product_name, brand_name, packing, scrap_date, quantity, current_price, unit_price, stock_status, rating, no_of_reviews, promotion_status)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

cur.executemany(insert_query, [(d["product_name"], d["brand_name"], d["packing"], d["scrap_date"], d["quantity"], d["current_price"], d["unit_price"], d["stock_status"], d["rating"], d["no_of_reviews"], d["promotion_status"]) for d in fact_pns_dict_list])
conn.commit()


import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host = "localhost",
    dbname = "retailer_proj", #change
    user = "postgres",
    password = "00000000", #change
    port = 5432
)
cur = conn.cursor()


df = pd.read_csv(file_name)

cur.execute("""
    CREATE TABLE IF NOT EXISTS product_pns (
        product_name VARCHAR(255),
        brand_name VARCHAR(255),
        category VARCHAR(255),
        packing VARCHAR(50),
        country VARCHAR(255),
        primary key(product_name, brand_name, packing)
    )
""")

conn.commit()

product_pns = pd.read_csv(file_name) 

product_name = product_pns["product_name"].tolist()
brand_name = product_pns["brand_name"].tolist()
category = product_pns["category"].tolist()
packing = product_pns["packing"].tolist()
country = product_pns["country"].tolist()

product_pns_dict_list = []
for a, b, c, d, e,  in zip(product_name, brand_name, category, packing, country):
    product = { 'product_name': a, 'brand_name': b, 'category': c, 'packing': d, 'country': e  }
    product_pns_dict_list.append(product)

# get the data from the database and convert to dict, for checking
product_name_check = pd.read_sql("SELECT product_name FROM product_pns", conn)
product_name_check =product_name_check.values.tolist()

brand_name_check = pd.read_sql("SELECT brand_name FROM product_pns", conn)
brand_name_check = brand_name_check.values.tolist()

packing_check = pd.read_sql("SELECT packing FROM product_pns", conn)
packing_check = packing_check.fillna('NaN')
packing_check = packing_check.values.tolist()

product_pns_check_list = []
for a, b, c  in zip(product_name_check, brand_name_check, packing_check):
    product = { 'product_name': a, 'brand_name': b, 'packing': c  }
    product_pns_check_list.append(product)
    
# Convert lists to strings
for d in product_pns_check_list:
    for key in d:
        if isinstance(d[key], list) and len(d[key]) == 1:  # Check if the value is a list with one element
            d[key] = d[key][0]  # Convert the list to a string
            
# Function to find dictionaries in list1 that do not match any dictionaries in list2 based on specific keys
def find_non_matching_dicts(list1, list2, keys):
    non_matching_list = []
    for d1 in list1:
        match_found = False
        for d2 in list2:
            if all(d1[key] == d2[key] for key in keys):
                match_found = True
                break  # Break the inner loop if a match is found
        if not match_found:
            non_matching_list.append(d1)
    return non_matching_list

# Keys to compare
keys_to_compare = ["product_name", "brand_name", "packing"]

# Usage
non_matching_dicts = find_non_matching_dicts(product_pns_dict_list, product_pns_check_list, keys_to_compare)

import math
def filter_products(products):
    new_list = []
    for product in products:
        if 'packing' in product and isinstance(product['packing'], float) and math.isnan(product['packing']):
            continue
        else:
            new_list.append(product)
    return new_list

further_filtered = filter_products(non_matching_dicts)

insert_query = """INSERT INTO product_pns ( product_name, brand_name, category, packing, country)
VALUES ( %s, %s, %s, %s, %s)"""

cur.executemany(insert_query, [( d["product_name"], d['brand_name'] ,d["category"], d["packing"], d["country"]) for d in further_filtered]) 
# cur.executemany(insert_query, [( d["product_name"], d['brand_name'] ,d["category"], d["packing"], d["country"]) for d in non_matching_dicts])

conn.commit()
cur.close()
conn.close()