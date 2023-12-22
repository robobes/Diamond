# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 16:46:26 2023

@author: PC
"""
from tefas import Crawler
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds


tefas = Crawler()
table = pa.Table.from_pandas(pd.DataFrame(tefas.fetch(start=datetime.today())))
ds.write_dataset(table, "./DATA/DATABASE/TEFAS",
                 format="parquet", partitioning=ds.partitioning(
                    pa.schema([table.schema.field("date")])),existing_data_behavior="overwrite_or_ignore")