# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 12:24:25 2024

@author: PC
"""

from fredapi import Fred
import pandas as pd
import matplotlib.pyplot as plt


fred = Fred(api_key='80d221ef8bc4d65b4d93d33df8e3be9e')

monthlytickers= ['CPIAUCSL']
count=0
for t in monthlytickers:
    data = fred.get_series(t)
    data.name=t
    if count==0:
        monthlyres=data
    else:
        monthlyres=pd.concat([monthlyres,data],axis=1)
    count+=1

qtickers = ["GDPC1"]
count=0
for t in qtickers:
    data = fred.get_series(t)
    data.name=t
    if count==0:
        qres=data
    else:
        qres=pd.concat([qres,data],axis=1)
    count+=1

dailytickers = ["DFF","USRECDM","DGS10","DGS2","DGS3MO"]
count=0
for t in dailytickers:
    data = fred.get_series(t)
    data.name=t
    if count==0:
        dailyres=data
    else:
        dailyres=pd.concat([dailyres,data],axis=1)
    count+=1

prox = pd.read_excel("https://www.frbsf.org/wp-content/uploads/proxy-funds-rate-data.xlsx?20240105",
              skiprows=9)[["Date","Proxy funds rate"]]
prox.columns=["Date","Proxy_funds_rate"]
prox["Date"]=prox["Date"].dt.to_period("M").dt.to_timestamp()
prox=prox.set_index("Date")
monthlyres = pd.concat([monthlyres,prox],
          axis=1 )
monthlytickers.append("Proxy_funds_rate")

aqr = pd.read_excel("https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Commodities-for-the-Long-Run-Index-Level-Data-Monthly.xlsx?sc_lang=en",
              skiprows=10)
dat=aqr[['Unnamed: 0','State of backwardation/contango']]
dat.columns=["date","commodity_curve"]
dat["date"] = pd.to_datetime(dat["date"]).dt.to_period("M").dt.to_timestamp()
dat = dat.set_index("date")
dat_dummy = pd.get_dummies(dat,columns=["commodity_curve"])

dat_dummy.columns
dat_dummy_2 = dat_dummy['commodity_curve_Backwardation']*-1 + dat_dummy["commodity_curve_Contango"]


c = 1
count_arr = [c]
for i in range(0,dat_dummy_2.shape[0]):
    if i==0:
        continue
    if dat_dummy_2.iloc[i] == dat_dummy_2.iloc[i-1]:
        c+=1
    else:
        c=1
    count_arr.append(c)

sums_count=[]
for i in range(0,len(count_arr)):
    if i > len(count_arr)-6:
        new = 22
    else:
        new =  sum(count_arr[i:i+6])
    sums_count.append(new)

for i in range(0,dat_dummy_2.shape[0]):
    if sums_count[i] < 21 and i > 0:
        dat_dummy_2.iloc[i] = dat_dummy_2.iloc[i-1]


dat_dummy_2.name="commodity_curve_Contango"

monthlyres = pd.concat([monthlyres,dat_dummy_2],
          axis=1 )
monthlytickers.append("commodity_curve_Contango")

## PLOTS

for t in monthlytickers:    
    plt.plot(monthlyres[t])
    plt.title(t)
    plt.show()


dummy3 = dat_dummy_2.loc["1925-12-01":]
plt.fill_between(dummy3.reset_index().date.values, dummy3.reset_index().commodity_curve_Contango.values == 1,color="green")
plt.fill_between(dummy3.reset_index().date.values, dummy3.reset_index().commodity_curve_Contango.values == -1,color="red")
plt.show()




for t in dailytickers:    
    plt.plot(dailyres[t])
    plt.title(t)
    plt.show()
    
for t in qtickers:    
    plt.plot(qres)
    plt.title(t)
    plt.show()