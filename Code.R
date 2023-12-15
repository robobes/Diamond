library(arrow)
library(tidyverse)

kyd <- open_dataset("./KYD")
res <- kyd %>% select(KYDALTINK) %>% slice(1)

save(res,"Output.RData")