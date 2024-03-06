library(tidyr)
library(tidyverse)
load("~/Github/Diamond/DATA/ANALYTICS/Output.RData")
mydat<-tibble(x=runif(param),y=runif(param))

dat <- read_csv("~/Github/Diamond/DATA/SHINY/regime_data.csv")
plotdat_inf_us <-  dat %>%  filter(Field =="INF_YOY",Country=="US") %>%   rename("Date"=...1) %>%  select(-Field2) %>%  na.omit
plotdat_gro_us <-  dat %>%  filter(Field =="GDP_YOY",Country=="US") %>%   rename("Date"=...1) %>%  select(-Field2) %>%  na.omit



save(mydat,plotdat_inf_us,plotdat_inf_us,file="~/Github/Diamond/DATA/SHINY/Data_for_shiny.RData")
