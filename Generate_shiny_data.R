load("Output.RData")
mydat<-tibble(x=runif(param),y=runif(param))
save(mydat,file="Data_for_shiny.RData")