library(tidyr)
library(tidyverse)
load("~/Github/Diamond/DATA/ANALYTICS/Output.RData")
mydat<-tibble(x=runif(param),y=runif(param))

dat <- read_csv("~/Github/Diamond/DATA/SHINY/regime_data.csv")
plotdat_inf_us <-  dat %>%  filter(Field =="INF_YOY",Country=="US") %>%   rename("Date"=...1) %>%  select(-Field2) %>%  na.omit
plotdat_gro_us <-  dat %>%  filter(Field =="GDP_YOY",Country=="US") %>%   rename("Date"=...1) %>%  select(-Field2) %>%  na.omit


colorpalette_inf <- c("DISINFLATION" = "darkolivegreen3", "FIRE" = "firebrick3",
                      "ICE"="lightsteelblue3","REFLATION"="navajowhite")
colorpalette_gro <- c("SLUMP" = "darkolivegreen3", "BOOM" = "firebrick3",
                      "RECESSION"="lightsteelblue3","RECOVERY"="navajowhite")


save(mydat,plotdat_inf_us,plotdat_gro_us,colorpalette_gro,colorpalette_inf,file="~/Github/Diamond/DATA/SHINY/Data_for_shiny.RData")
