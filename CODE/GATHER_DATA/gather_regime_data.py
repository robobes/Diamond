# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 12:24:25 2024

@author: PC
"""

from fredapi import Fred
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandasdmx as sdmx

#FRED Daily, Quarterly, Monthly
fred = Fred(api_key='80d221ef8bc4d65b4d93d33df8e3be9e')

monthlytickers= ['CPIAUCSL','FEDFUNDS']
count=0
for t in monthlytickers:
    data = fred.get_series(t)
    data.name=t
    if count==0:
        monthlyres=data
    else:
        monthlyres=pd.concat([monthlyres,data],axis=1)
    count+=1

qtickers = ["GDPC1","USRECQ"]
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
raw_commodity_data = dat
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


    
#Calculate regimes

### Inflation

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
                
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)


#Inflation regime
Inf_yoy = monthlyres["CPIAUCSL"].pct_change(12).dropna()


zz_inf = FindTurningPoints_inf(price=Inf_yoy,threshold_up=0.015,threshold_down=-0.015)
plotdat = zz_inf.rename(columns={"CPIAUCSL":"Price"})

plotdat = pd.merge_asof(pd.DataFrame(index=pd.date_range("1948-01-01",plotdat.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              plotdat,right_index=True,left_index=True)


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


#### Growth


def FindTurningPoints_gro(price,threshold_up,threshold_down):
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
    dates_trend_change = dates_trend_change.append(price.index[-2:-1])
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="BOOM"
    else:
        pivots2.iloc[0]="RECOVERY"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])
        
        
        if direction > 0:
            if min(price_chunk) > 0.05:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            elif max(price_chunk) < -0.01:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
            elif min(price_chunk) < -0.01:
                dt_new =  price_chunk[(price_chunk[price_chunk < 0]).index].tail(1).index
                pivots2[dt_start]="RECOVERY"
                final_pivot_dates.append(dt_new)
                pivots2[dt_new]="BOOM"
            elif min(price_chunk) < 0.02 and max(price_chunk) > 0.05:
                dt_new = price_chunk[(price_chunk - 0.02) < 0].tail(1).index
                final_pivot_dates.append(dt_start)
                final_pivot_dates.append(dt_new)
                pivots2[dt_start]="RECOVERY"
                pivots2[dt_new]="BOOM"
            elif min(price_chunk) > 0.02 and max(price_chunk) > 0.05:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
        elif direction < 0:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="SLUMP"
                
    # Labels df
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)


gdp_yoy = qres['GDPC1'].pct_change(4).dropna()
nber_rec = qres['USRECQ']


zz_growth= FindTurningPoints_gro(gdp_yoy, threshold_up=0.01, threshold_down=-0.01)
plotdat = pd.concat([zz_growth,nber_rec],axis=1).dropna()
plotdat['Regime'] = plotdat['Regime'].where(plotdat["USRECQ"]==0,"RECESSION")



plotdat = pd.merge_asof(pd.DataFrame(index=pd.date_range("1948-01-01",plotdat.index[-1] + pd.Timedelta(days=100), freq="Q",inclusive="right")),
              plotdat,right_index=True,left_index=True)


plotdat = plotdat.rename(columns={"GDPC1":"Price"})
zz_growth = plotdat.drop(["USRECQ"],axis=1)
plt.plot(plotdat["Price"])
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BOOM") / 5),color="red",alpha=0.2,label='BOOM')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BOOM") / 25),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECESSION") / 5),color="blue",alpha=0.2,label='RECESSION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECESSION") / 25),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "SLUMP") / 5),color="green",alpha=0.2,label='SLUMP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "SLUMP") / 25),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECOVERY") / 5),color="yellow",alpha=0.2,label='RECOVERY')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECOVERY") / 25),color="yellow",alpha=0.2)

plt.legend()
plt.show()

#### Yield Curve



def FindTurningPoints_yc(level,slope,threshold_up,threshold_down):
    # Find turning points
    PEAK = 1
    VALLEY = -1
    
    up_thresh = threshold_up
    down_thresh = threshold_down
    
    if down_thresh > 0:
        raise ValueError('The down_thresh must be negative.')
        
    X = level.values
    initial_pivot = VALLEY if X[0] < X[-1] else PEAK
    t_n = len(X)
    pivots_level = np.zeros(t_n, dtype=np.int_)
    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = X[0]

    pivots_level[0] = initial_pivot

    for t in range(1, t_n):
        x = X[t]
        r = x - last_pivot_x

        if trend == -1:
            if r >= up_thresh:
                pivots_level[last_pivot_t] = trend
                trend = PEAK
                last_pivot_x = x
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            if r <= down_thresh:
                pivots_level[last_pivot_t] = trend
                trend = VALLEY
                last_pivot_x = x
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
                
    X = slope.values
    initial_pivot = VALLEY if X[0] < X[-1] else PEAK
    t_n = len(X)
    pivots_slope = np.zeros(t_n, dtype=np.int_)
    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = X[0]

    pivots_slope[0] = initial_pivot

    for t in range(1, t_n):
        x = X[t]
        r = x - last_pivot_x

        if trend == -1:
            if r >= up_thresh:
                pivots_slope[last_pivot_t] = trend
                trend = PEAK
                last_pivot_x = x
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            if r <= down_thresh:
                pivots_slope[last_pivot_t] = trend
                trend = VALLEY
                last_pivot_x = x
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t

    # Analyze each trend period
    pivots = abs(pivots_level) + abs(pivots_slope)
    dates_trend_change=level.index[np.nonzero(pivots)]
    dates_trend_change = dates_trend_change.append(level.index[-2:-1])
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=level.index)
    
    pivots2[0] = "BULL_STEEP"

    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        level_chunk=level.loc[dt_start:dt_end]
        level_direction= np.sign(level_chunk[-1]-level_chunk[0])
        slope_chunk=slope.loc[dt_start:dt_end]
        slope_direction= np.sign(slope_chunk[-1]-slope_chunk[0])
        
        
        
        if level_direction > 0:
            if slope_direction > 0:
                pivots2[dt_start]="BEAR_STEEP"
            else:
                pivots2[dt_start]="BEAR_FLAT"
        else:
            if slope_direction > 0:
                pivots2[dt_start]="BULL_STEEP"
            else:
                pivots2[dt_start]="BULL_FLAT"
        

    # Labels df
    labels=pd.DataFrame({"Level":level,'Slope':slope,"Regime":pivots2.ffill()},index=level.index)
    
    return({"Labels":labels})


YC = dailyres[['DGS10','DGS3MO']].dropna()
YC = pd.concat([YC,
           (YC.mean(axis=1)),
           ((YC["DGS10"] - YC["DGS3MO"])),
           ((YC["DGS10"] - YC["DGS3MO"]) < 0)],axis=1)
YC.columns=['DGS10','DGS3MO','level','slope','inverted']


zz_yc = FindTurningPoints_yc(level=YC['level'],slope= YC['slope'], threshold_up=1, threshold_down=-1)["Labels"]
zz_yc['Regime'] = np.where( YC['inverted'],"INVERTED",zz_yc['Regime'])



plotdat = zz_yc



plt.plot(plotdat["Slope"]/100)
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "INVERTED") / 14),color="maroon",alpha=0.3,label='INVERTED')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "INVERTED") / 40),color="maroon",alpha=0.3)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BEAR_FLAT") / 14),color="blue",alpha=0.3,label='BEAR_FLAT')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BEAR_FLAT") / 40),color="blue",alpha=0.3)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BULL_STEEP") / 14),color="green",alpha=0.3,label='BULL_STEEP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BULL_STEEP") / 40),color="green",alpha=0.3)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BEAR_STEEP") / 14),color="orangered",alpha=0.3,label='BEAR_STEEP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BEAR_STEEP") / 40),color="orangered",alpha=0.3)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BULL_FLAT") / 14),color="yellow",alpha=0.3,label='BULL_FLAT')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BULL_FLAT") / 40),color="yellow",alpha=0.3)
plt.legend()
plt.show()


### fed funds


def FindTurningPoints_fed(price,threshold_up,threshold_down):
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
    dates_trend_change = dates_trend_change.append(price.index[-2:-1])
    dates_trend_change = dates_trend_change.delete([9,10,18,22])
    dates_trend_change = dates_trend_change.append(price.index[716:717])
    dates_trend_change = dates_trend_change.append(price.index[532:533])
    dates_trend_change = dates_trend_change.sort_values()
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="TIGHTENING"
    else:
        pivots2.iloc[0]="LOOSENING"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])

        
        if direction > 0:
            final_pivot_dates.append(dt_start)
            pivots2[dt_start]="TIGHTENING"

        elif direction < 0:
            final_pivot_dates.append(dt_start)
            pivots2[dt_start]="LOOSENING"
                
    # Labels df
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)

fedfunds = monthlyres[['FEDFUNDS','Proxy_funds_rate'] ]
fedfunds["Rate"] = np.where(np.isnan(fedfunds["Proxy_funds_rate"]),fedfunds['FEDFUNDS'],fedfunds["Proxy_funds_rate"])
fedfunds = fedfunds["Rate"].dropna()


zz_fed = FindTurningPoints_fed(fedfunds, threshold_up=2, threshold_down=-2)
plotdat = zz_fed
plt.plot(plotdat["Rate"]/100)
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "TIGHTENING") / 5),color="maroon",alpha=0.3,label='TIGHTENING')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "TIGHTENING") / 40),color="maroon",alpha=0.3)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "LOOSENING") / 5),color="green",alpha=0.3,label='LOOSENING')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "LOOSENING") / 40),color="green",alpha=0.3)
plt.legend()
plt.show()



## Commodity
'''
plotdat = monthlyres["commodity_curve_Contango"].dropna()


plotdat = pd.merge_asof(pd.DataFrame(index=pd.date_range("1877-02-01",plotdat.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              plotdat,right_index=True,left_index=True)

plt.fill_between(plotdat.index, (np.array(plotdat.values == 1) / 5),color="green",alpha=0.3,label='CONTANGO')

plt.fill_between(plotdat.index, (np.array(plotdat.values == -1) / 5),color="maroon",alpha=0.3,label='BACKWARDATION')

plt.legend()
plt.show()
'''

# Turkey EVDS

#Turkey growth

def FindTurningPoints_grotr(price,threshold_up,threshold_down):
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
    dates_trend_change = dates_trend_change.append(price.index[-2:-1])
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="BOOM"
    else:
        pivots2.iloc[0]="RECOVERY"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])
        
        
        if direction > 0:
            if min(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            elif max(price_chunk) < 0.03:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
            elif min(price_chunk) < 0.03 and max(price_chunk) > 0.08:
                dt_new =  price_chunk[(price_chunk[(price_chunk - 0.03) < 0]).index].tail(1).index
                pivots2[dt_start]="RECOVERY"
                final_pivot_dates.append(dt_new)
                pivots2[dt_new]="BOOM"
            elif min(price_chunk) > 0.03 and max(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
        elif direction < 0:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="SLUMP"
                
    # Labels df
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)

    
    
from evds import evdsAPI
evds_api_key = "gHOEMBlsbI"
evds = evdsAPI(evds_api_key)
gdp_tr = evds.get_data(["TP.UR.G23","TP.GSYIH26.HY.ZH"],startdate ="01-01-1987",enddate="01-02-2030",formulas=[0,0])
gdp_tr.index = pd.to_datetime(gdp_tr["Tarih"]).rename("Date")
gdp_tr = gdp_tr.drop(["Tarih"],axis=1).pct_change(4)
gdp_tr['value'] = np.where(np.isnan(gdp_tr["TP_GSYIH26_HY_ZH"]),gdp_tr['TP_UR_G23'],gdp_tr['TP_GSYIH26_HY_ZH'])
gdp_tr = gdp_tr['value'].dropna()



plotdat = FindTurningPoints_grotr(gdp_tr, threshold_up=0.03, threshold_down=-0.03).dropna()


recessiondates = pd.to_datetime(["1988-Q4",	"1989-Q1",	"1994-Q2",	"1994-Q3",		"1998-Q4",	"1999-Q1",	"1999-Q2",
                                 "2001-Q2",	"2001-Q3",	"2001-Q4",	"2008-Q3",	"2008-Q4",	"2009-Q1",	"2018-Q3",	"2018-Q4",	"2019-Q1",	"2020-Q2"])
plotdat = plotdat.merge(pd.DataFrame({"value":1},index=recessiondates),how='left',left_index=True,right_index=True)
plotdat['Regime'] = np.where(np.isnan(plotdat['value']),plotdat['Regime'],"RECESSION")


plotdat = pd.merge_asof(pd.DataFrame(index=pd.date_range("1988-04-01",pd.Timestamp.now(), freq="Q")),
              plotdat,right_index=True,left_index=True).drop(columns=["value"])



plt.plot(plotdat["Price"])
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BOOM") / 5),color="red",alpha=0.2,label='BOOM')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BOOM") / 25),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECESSION") / 5),color="blue",alpha=0.2,label='RECESSION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECESSION") / 25),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "SLUMP") / 5),color="green",alpha=0.2,label='SLUMP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "SLUMP") / 25),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECOVERY") / 5),color="yellow",alpha=0.2,label='RECOVERY')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECOVERY") / 25),color="yellow",alpha=0.2)

plt.legend()
plt.show()

zz_gro_tr =plotdat

#Turkey Inf



def FindTurningPoints_inf_tr(price,threshold_up,threshold_down):
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
                
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)


inf_tr = evds.get_data(["TP.TUFE1YI.T1"],startdate ="01-01-1982",enddate="01-02-2030",formulas=[0,0])
inf_tr.index = pd.to_datetime(inf_tr["Tarih"]).rename("Date") 
inf_tr = inf_tr.drop(["Tarih"],axis=1).pct_change(12).dropna()

zz_inf_tr = FindTurningPoints_inf_tr(price=inf_tr.squeeze(),threshold_up=0.03,threshold_down=-0.03)
plotdat = zz_inf_tr

plotdat = pd.merge_asof(pd.DataFrame(index=pd.date_range("1983-01-01",plotdat.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              plotdat,right_index=True,left_index=True)

plotdat = plotdat.rename(columns={"TP_TUFE1YI_T1":"Price"})
plt.plot(plotdat["Price"])
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "FIRE") / 0.606),color="red",alpha=0.2,label='FIRE')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "FIRE") / 25),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "ICE") / 0.606),color="blue",alpha=0.2,label='ICE')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "ICE") / 25),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "DISINFLATION") / 0.606),color="green",alpha=0.2,label='DISINFLATION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "DISINFLATION") / 25),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "REFLATION") / 0.606),color="yellow",alpha=0.2,label='REFLATION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "REFLATION") / 25),color="yellow",alpha=0.2)

plt.legend()
plt.show()


#CLIs

start = '1955-01-01'
end = '2024-02-01'
oecd = sdmx.Request('OECD')
params = dict(startPeriod=start, endPeriod=end)
data_msg = oecd.data('MEI_CLI', key='LOLITOAA.TUR+USA.M', params=params)
data = data_msg.data[0]
CLI = sdmx.to_pandas(data).unstack()

CLI.index = CLI.index.droplevel([0,2])
CLI = CLI.transpose()

### CLI US




def FindTurningPoints_cli_us(price,threshold_up,threshold_down):
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
    dates_trend_change = dates_trend_change.append(price.index[-2:-1])
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="BOOM"
    else:
        pivots2.iloc[0]="RECOVERY"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])
        
        
        if direction > 0:
            if min(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            elif max(price_chunk) < 0.03:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
            elif min(price_chunk) < 0.03 and max(price_chunk) > 0.08:
                dt_new =  price_chunk[(price_chunk[(price_chunk - 0.03) < 0]).index].tail(1).index
                pivots2[dt_start]="RECOVERY"
                final_pivot_dates.append(dt_new)
                pivots2[dt_new]="BOOM"
            elif min(price_chunk) > 0.03 and max(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
        elif direction < 0:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="SLUMP"
                
    # Labels df
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)


cli_us = CLI["USA"]
zz_cli_us = FindTurningPoints_cli_us(cli_us, threshold_up=3, threshold_down=-3)
plotdat =zz_cli_us.rename(columns={"USA":"Price"})


plt.plot(plotdat["Price"]-100)
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BOOM") *5),color="red",alpha=0.2,label='BOOM')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BOOM") *7),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECESSION") *5),color="blue",alpha=0.2,label='RECESSION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECESSION") *7),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "SLUMP") *5),color="green",alpha=0.2,label='SLUMP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "SLUMP") *7),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECOVERY") *5),color="yellow",alpha=0.2,label='RECOVERY')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECOVERY") *7),color="yellow",alpha=0.2)

plt.legend()
plt.show()



### CLI TR

def FindTurningPoints_cli_tr(price,threshold_up,threshold_down):
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
    dates_trend_change = dates_trend_change.append(price.index[-2:-1])
    pivots2=pd.Series(np.empty(len(pivots)).fill(np.NaN),index=price.index)
    
    if pivots[0] == 1 :
        pivots2.iloc[0]="BOOM"
    else:
        pivots2.iloc[0]="RECOVERY"
    
    
    final_pivot_dates=[]
    for i in range(1,len(dates_trend_change)):
        dt_start=dates_trend_change[i-1]
        dt_end=dates_trend_change[i]
        
        if i == len(dates_trend_change)-1:
            final_pivot_dates.append(dt_end)
        price_chunk=price.loc[dt_start:dt_end]
        direction= np.sign(price_chunk[-1]-price_chunk[0])
        
        
        if direction > 0:
            if min(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            elif max(price_chunk) < 0.03:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
            elif min(price_chunk) < 0.03 and max(price_chunk) > 0.08:
                dt_new =  price_chunk[(price_chunk[(price_chunk - 0.03) < 0]).index].tail(1).index
                pivots2[dt_start]="RECOVERY"
                final_pivot_dates.append(dt_new)
                pivots2[dt_new]="BOOM"
            elif min(price_chunk) > 0.03 and max(price_chunk) > 0.08:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="BOOM"
            else:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="RECOVERY"
        elif direction < 0:
                final_pivot_dates.append(dt_start)
                pivots2[dt_start]="SLUMP"
                
    # Labels df
    res = pd.concat([price,pivots2.shift(1).ffill()],axis=1).rename(columns={"value": "Price", 0: "Regime"})

    
    return(res)


cli_tr = CLI["TUR"].dropna()
zz_cli_tr = FindTurningPoints_cli_tr(cli_tr, threshold_up=3, threshold_down=-3)
plotdat =zz_cli_tr.rename(columns={"TUR":"Price"})


plt.plot(plotdat["Price"]-100)
plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "BOOM") *10),color="red",alpha=0.2,label='BOOM')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "BOOM") *25),color="red",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECESSION") *10),color="blue",alpha=0.2,label='RECESSION')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECESSION") *25),color="blue",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "SLUMP") *10),color="green",alpha=0.2,label='SLUMP')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "SLUMP") *25),color="green",alpha=0.2)

plt.fill_between(plotdat.index, (np.array(plotdat.Regime.values == "RECOVERY") *10),color="yellow",alpha=0.2,label='RECOVERY')
plt.fill_between(plotdat.index, -1*(np.array(plotdat.Regime.values == "RECOVERY") *25),color="yellow",alpha=0.2)

plt.legend()
plt.show()

### combine all data

df = zz_inf  
df["Country"]="US"
df["Field"]="INF_YOY"
df["Field2"]=None
df = df.rename(columns={"Price":"Value"})
result = df 

df = zz_growth
df["Country"]="US"
df["Field"]="GDP_YOY"
df["Field2"]=None
df = df.rename(columns={"Price":"Value"})
result = pd.concat([result,df])


df = zz_fed
df["Country"]="US"
df["Field"]="FED_FUNDS"
df["Field2"]=None
df = df.rename(columns={"Rate":"Value"})
pd.concat([result,df])


df = zz_yc
df.index.name="Date"
df = df.rename(columns={"Level":"YC_level","Slope":"YC_slope"})
df = pd.melt(df,value_vars=["YC_level","YC_slope"],id_vars="Regime",ignore_index=False,value_name="Value")
df = df.rename(columns={"variable":"Field2"})
df["Field"]="Yield_Curve"
result = pd.concat([result,df])

df = zz_cli_us
df.index = pd.to_datetime(df.index)
df = pd.merge_asof(pd.DataFrame(index=pd.date_range("1955-01-01",df.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              df,right_index=True,left_index=True)
df["Country"]="US"
df["Field"]="CLI"
df["Field2"]=None
df = df.rename(columns={"USA":"Value"})
result = pd.concat([result,df])


df = zz_inf_tr
df["Country"]="TR"
df["Field"]="INF_YOY"
df["Field2"]=None
df = df.rename(columns={"TP_TUFE1YI_T1":"Value"})
result = pd.concat([result,df])

df = zz_cli_tr
df.index = pd.to_datetime(df.index)
df = pd.merge_asof(pd.DataFrame(index=pd.date_range("1955-01-01",df.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              df,right_index=True,left_index=True)
df["Country"]="TR"
df["Field"]="CLI"
df["Field2"]=None
df = df.rename(columns={"TUR":"Value"})
result = pd.concat([result,df])


df = zz_gro_tr
df["Country"]="TR"
df["Field"]="GDP_YOY"
df["Field2"]=None
df = df.rename(columns={"Price":"Value"})
result = pd.concat([result,df])

df = raw_commodity_data
df.index = pd.to_datetime(df.index)
df = pd.merge_asof(pd.DataFrame(index=pd.date_range("1877-02-01",df.index[-1] + pd.Timedelta(days=30), freq="M",inclusive="right")),
              df,right_index=True,left_index=True)
df["Country"]="US"
df["Field"]="Commodity_Curve"
df["Value"]=0
df["Field2"]=None
df = df.rename(columns={"commodity_curve":"Regime"})
result = pd.concat([result,df])


#### save the data

result.to_csv( 'C:/Users/PC/Documents/Github/Diamond/DATA/SHINY/regime_data.csv')

