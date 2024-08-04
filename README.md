## A tool of monitoring non-alcoholic products at HKTVmall, PNS, and Wellcome on a daily basis.

### Project Overview
This project aims to analyze the beverage market in Hong Kong by scraping data from major retailer websites, importing the data into a database, and then generating visualizations to gain insights.

### Analysis Description:
Data Collection
The data for this project was obtained by scraping the websites of the following 3 major beverage retailers in Hong Kong:
HKTVmall
Parknshop
Wellcome

A custom web scraper was developed using Python and the Selenium library to extract relevant product information, for instance, brand, price, category and sales quantity.

### Data Storage
The scraped data was then imported into a PostgreSQL database for further analysis. The database schema includes the following tables:

`products`: Stores information about each beverage product, including brand, category, price, and other relevant details.
`sales`: Stores historical sales data for the beverage products, if available.


### Data Analysis
The data stored in the database was then analyzed using various visualization techniques, including:

Bar charts to compare sales and pricing across different beverage categories
Line charts to track changes in sales over time
Scatter plots to identify any relationships between product attributes and sales performance

#### Best-Selling Products： 
<img src="https://github.com/liaolisha/Beverage-HK/blob/main/%E5%9B%BE%E7%89%871.png" data-canonical-src="https://github.com/liaolisha/Beverage-HK/blob/main/%E5%9B%BE%E7%89%871.png" width="600" height="500" />

### Usage
To run the project, you will need to have the following dependencies installed:

- Python 3.11.9
- PostgreSQL
- Python libraries:
- Selenium
- Pandas
- Matplotlib
- Seaborn




To get started, follow these steps:

1. Clone the repository to your local machine.
2. Set up the PostgreSQL database and update the connection details in the respective `import_to_db.py` file.
3. Run the web scraper script to collect the data.
4. Run the analysis scripts to generate the visualizations.

The specific steps for each of these tasks are detailed in the individual script files and their corresponding documentation.

### Contributions
If you have any suggestions or improvements for this project, feel free to open an issue or submit a pull request. We welcome contributions from the community.

