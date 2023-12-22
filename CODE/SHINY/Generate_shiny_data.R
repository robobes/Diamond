library(tidyr)
load("DATA/ANALYTICS/Output.RData")
mydat<-tibble(x=runif(param),y=runif(param))
save(mydat,file="DATA/SHINY/Data_for_shiny.RData")
