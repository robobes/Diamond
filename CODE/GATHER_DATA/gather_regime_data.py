# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 12:24:25 2024

@author: PC
"""

from fredapi import Fred
import pandas as pd
import matplotlib.pyplot as plt
import zigzag as zz
import numpy as np

#FRED Daily, Quarterly, Monthly
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
    
# Proxy Fed funds SanFransisco Fed
prox = pd.read_excel("https://www.frbsf.org/wp-content/uploads/proxy-funds-rate-data.xlsx?20240105",
              skiprows=9)[["Date","Proxy funds rate"]]
prox.columns=["Date","Proxy_funds_rate"]
prox["Date"]=prox["Date"].dt.to_period("M").dt.to_timestamp()
prox=prox.set_index("Date")
monthlyres = pd.concat([monthlyres,prox],
          axis=1 )
monthlytickers.append("Proxy_funds_rate")

#AQR commodity curve Contango / backwardation
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

## PLOTS to check

for t in monthlytickers:    
    plt.plot(monthlyres[t])
    plt.title(t)
    plt.show()

### aqr curve plot
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
    
    
#Calculate regimes



def FindTurningPoints(price,threshold_up,threshold_down):
    # Find turning points
    pivots = zz.peak_valley_pivots(price.values, threshold_up, threshold_down)
    modes = zz.pivots_to_modes(pivots)
    ts_pivots = pd.Series(price, index=price.index)
    ts_pivots = ts_pivots[pivots != 0]

    # Label turning points
    labels_turning_points=pivots.astype(str)
    labels_turning_points[labels_turning_points=="1"]="ToDownTrend"
    labels_turning_points[labels_turning_points== "-1"]="ToUpTrend"

    # Label trend direction
    labels_trend=modes
   
    # Labels df
    labels=pd.DataFrame({"Price":price,"TurningPoints":labels_turning_points,"Trend":labels_trend},index=price.index)

    # Analyze each trend period
    dates_trend_change=price.index[np.nonzero(pivots)]
    chunks=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        price_chunk=price.loc[dt_start:dt_end]
        ret_chunk=price_chunk.pct_change().dropna()
        duration=(dt_end-dt_start)/ np.timedelta64(1, 'D')
        total_ret=(price_chunk[-1]/price_chunk[0])-1
        cagr=(price_chunk[-1]/price_chunk[0])**(365/duration)-1
        direction=np.sign(total_ret)
        vol=np.std(ret_chunk)
        dd=price_chunk.div(price_chunk.cummax())-1
        add=0.75*np.quantile(dd,0.5)+0.25*np.quantile(dd,0.90)
        chunks.append({"Start":dt_start,"End":dt_end,"Duration":duration,\
                       "Return":total_ret,"CAGR":cagr,\
                       "Direction":direction,"Volatility":vol,"AvgDD":add})
    chunks=pd.DataFrame(chunks)    

    return({"Labels":labels,"Chunks":chunks})

def FindTurningPoints_inf(price,threshold_up,threshold_down):
    # Find turning points
    PEAK = 1
    VALLEY = -1
    
    up_thresh = threshold_up
    down_thresh = threshold_down
    
    if down_thresh > 0:
        raise ValueError('The down_thresh must be negative.')
        
    X = price.values
    initial_pivot = VALLEY if X[0] < X[-1] else PEAK
    t_n = len(X)
    pivots = np.zeros(t_n, dtype=np.int_)
    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = X[0]

    pivots[0] = initial_pivot

    for t in range(1, t_n):
        x = X[t]
        r = x - last_pivot_x

        if trend == -1:
            if r >= up_thresh:
                pivots[last_pivot_t] = trend
                trend = PEAK
                last_pivot_x = x
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            if r <= down_thresh:
                pivots[last_pivot_t] = trend
                trend = VALLEY
                last_pivot_x = x
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t

    # Analyze each trend period
    dates_trend_change=price.index[np.nonzero(pivots)]
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="FIRE"
    else:
        pivots2.iloc[0]="ICE"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])
        
        if dt_start == pd.to_datetime('2008-07-01'):
            final_pivot_dates.append(dt_start)
            pivots2[dt_start]="ICE"
            continue
        
        if direction > 0:
            if min(price_chunk) > 0.05:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="FIRE"
            elif max(price_chunk) < -0.01:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="ICE"
            elif min(price_chunk) < -0.01:
                dt_new =  price_chunk[(price_chunk[price_chunk < 0] + 0.01 < 0).index].tail(1).index
                pivots2[dt_start]="ICE"
                final_pivot_dates.append(dt_new)
                pivots2[dt_new]="REFLATION"
            elif min(price_chunk) < 0.02 and max(price_chunk) > 0.05:
                dt_new = price_chunk[(price_chunk - 0.02) < 0].tail(1).index
                final_pivot_dates.append(dt_start)
                final_pivot_dates.append(dt_new)
                pivots2[dt_start]="REFLATION"
                pivots2[dt_new]="FIRE"
            elif min(price_chunk) > 0.02 and max(price_chunk) > 0.05:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="FIRE"
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="REFLATION"
        elif direction < 0:
            if max(price_chunk) < -0.01:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="ICE"
            elif min(price_chunk) < -0.01 and max(price_chunk) > 0.01:
                dt_new =  price_chunk[price_chunk[(price_chunk > -0.01) & (price_chunk < 0.01)].index].head(1).index
                pivots2[dt_start]="DISINFLATION"
                pivots2[dt_new]="ICE"
                final_pivot_dates.append(dt_start)
                final_pivot_dates.append(dt_new)
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="DISINFLATION"
                
    # Labels df
    labels=pd.DataFrame({"Price":price,"Regime":pivots2.ffill()},index=price.index)
    
    return({"Labels":labels})

#Guide: delete later
abc = FindTurningPoints(price=dailyres["DGS10"].dropna(),threshold_up=0.1,threshold_down=-0.1)
pd.melt(pd.DataFrame(abc["Labels"]["Trend"]).reset_index(),id_vars=["index"])

#Inflation regime
Inf_yoy = monthlyres["CPIAUCSL"].pct_change(12).dropna()


zz_inf = FindTurningPoints_inf(price=Inf_yoy,threshold_up=0.015,threshold_down=-0.015)
plotdat = zz_inf["Labels"]
plt.plot(plotdat["Price"])
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "FIRE") / 5),color="red",alpha=0.2,label='FIRE')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "FIRE") / 25),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "ICE") / 5),color="blue",alpha=0.2,label='ICE')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "ICE") / 25),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "DISINFLATION") / 5),color="green",alpha=0.2,label='DISINFLATION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "DISINFLATION") / 25),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "REFLATION") / 5),color="yellow",alpha=0.2,label='REFLATION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "REFLATION") / 25),color="yellow",alpha=0.2)

plt.legend()
plt.show()















