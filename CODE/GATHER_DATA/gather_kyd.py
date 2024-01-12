# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 16:39:29 2024

@author: PC
"""
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pyarrow as pa
import pyarrow.dataset as ds

url_list=open("./CODE/GATHER_DATA/kyd_urls.txt").readlines()
count = 0
for url in url_list:
    url_list[count] = url[:-1]
    count += 1



res = pd.DataFrame(columns=['Ticker', 'Name', 'Date' , 'Value'])
driver = webdriver.Chrome()

for url in url_list:
    driver.get(url)
    time.sleep(2)
    dates = driver.execute_script('return Highcharts.charts[0].series[0].data.map(x => x.series).map(x => x.xData)[0].map(x => new Date(x).toISOString())')
    values = driver.execute_script('return Highcharts.charts[0].series[0].data.map(x => x.series).map(x => x.yData)[0]')
    name=driver.find_element(by=By.XPATH,value='//h2').text
    ticker=driver.find_element(by=By.XPATH,value='//*[@id="printableArea"]/div/div[2]/div[2]/table/tbody/tr[1]/td[2]').text
    df = pd.DataFrame({'Ticker':ticker, 'Name':name, 'Date': dates, 'Value': values })
    res=pd.concat([res,df])
    
driver.quit()

res['Date']=pd.to_datetime(res['Date']).dt.date
table = pa.Table.from_pandas(res)
ds.write_dataset(table, "./DATA/DATABASE/KYD",
                 format="parquet", partitioning=ds.partitioning(
                    pa.schema([table.schema.field("Date")])),existing_data_behavior="overwrite_or_ignore")