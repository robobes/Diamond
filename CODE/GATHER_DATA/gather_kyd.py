# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 16:39:29 2024

@author: PC
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

import pandas as pd
import time
import pyarrow as pa
import pyarrow.dataset as ds

#chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
chrome_service = Service("/usr/lib/chromium-browser/chromedriver")


chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium-browser" # or /usr/bin/chromium
options = [
    "--headless",
    "--disable-gpu",
    "--window-size=1920,1200",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]
for option in options:
    chrome_options.add_argument(option)



url_list=open("./CODE/GATHER_DATA/kyd_urls.txt").readlines()
count = 0
for url in url_list:
    url_list[count] = url[:-1]
    count += 1




res = pd.DataFrame(columns=['Ticker', 'Name', 'Date', 'Value'])
failed_urls = []  # Track failed URLs


try:
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    
    for url in url_list:
        try:
            driver.get(url)
            max_attempts = 3
            success = False
            
            for attempt in range(max_attempts):
                time.sleep(3)
                try:
                    whichchart = driver.execute_script('return Highcharts.charts.length')
                    if whichchart > 0:
                        dates = driver.execute_script('return Highcharts.charts['+str(whichchart-1)+'].series[0].data.map(point => new Date(point.x).toISOString())')
                        values = driver.execute_script('return Highcharts.charts['+str(whichchart-1)+'].series[0].data.map(point => point.y)')
                        name = driver.find_element(by=By.XPATH,value='//h2').text
                        ticker = driver.find_element(by=By.XPATH,value='//*[@id="printableArea"]/div/div[2]/div[2]/table/tbody/tr[1]/td[2]').text
                        
                        df = pd.DataFrame({'Ticker':ticker, 'Name':name, 'Date': dates, 'Value': values })
                        if res.shape[0] == 0:
                            res = df
                        else:
                            res = pd.concat([res,df])
                        success = True
                        logging.info(f"Successfully processed: {url}")
                        break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e  # Re-raise on last attempt
                    continue
                    
            if not success:
                raise Exception("Max attempts reached without success")
                
        except Exception as e:
            failed_urls.append(url)
            logging.error(f"Failed to process URL: {url}")
            logging.error(f"Error: {str(e)}")
            continue

finally:
    driver.quit()
    
# Only proceed with database update if we have some successful results
if res.shape[0] > 0:
    try:
        res['Date'] = pd.to_datetime(res['Date']).dt.date
        res["update"] = 2

        dat = ds.dataset("./DATA/DATABASE/KYD", partitioning=["Ticker"]).to_table().to_pandas()
        dat["update"] = 1

        dataf = pd.concat([res,dat], ignore_index=True).sort_values('update', ascending=False).drop_duplicates(["Ticker","Date"]).drop(["update"],axis=1)
        dataf = dataf.reset_index().drop("index",axis=1)

        table = pa.Table.from_pandas(dataf)
        ds.write_dataset(table, "./DATA/DATABASE/KYD",
                        format="parquet", 
                        partitioning=ds.partitioning(pa.schema([table.schema.field("Ticker")])),
                        existing_data_behavior="overwrite_or_ignore")
        
        print(f"Database successfully updated with {res.shape[0]} new records")
        if failed_urls:
            logging.warning(f"Failed URLs ({len(failed_urls)}):")
            for url in failed_urls:
                logging.warning(f"  - {url}")
    
    except Exception as e:
        logging.error("Error during database update:")
        logging.error(str(e))
        raise
else:
    logging.warning("No data was collected successfully. Database not updated.")
