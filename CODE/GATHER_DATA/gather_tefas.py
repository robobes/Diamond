# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 16:46:26 2023

@author: PC
"""
from tefas import Crawler
from datetime import datetime, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds



tefas = Crawler()

df = pd.DataFrame(tefas.fetch(start=datetime.today()-timedelta(days=5),end=datetime.today()))

df['date'] = pd.to_datetime(df['date'])
df["mon"] = pd.DatetimeIndex(df['date']).month
df["year"] = pd.DatetimeIndex(df['date']).year
df["yearmon"] = df["year"].apply(str) +"_"+ df["mon"].apply(str)
df = df.drop(["mon","year"],axis=1)

df["update"]=2

dat = ds.dataset("./DATA/DATABASE/TEFAS",partitioning=["yearmon"]).to_table().to_pandas()
dat["update"]=1

dataf=pd.concat([df,dat],ignore_index=True).sort_values('update', ascending=False).drop_duplicates(["code","date"]).drop(["update"],axis=1)
dataf.reset_index().drop("index",axis=1)

table = pa.Table.from_pandas(dataf)
ds.write_dataset(table, "./DATA/DATABASE/TEFAS",
                 format="parquet", partitioning=ds.partitioning(
                    pa.schema([table.schema.field("yearmon")])),existing_data_behavior="overwrite_or_ignore")
