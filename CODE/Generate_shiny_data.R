library(tidyr)
load("DATA/Output.RData")
mydat<-tibble(x=runif(param),y=runif(param))
save(mydat,file="DATA/Data_for_shiny.RData")
