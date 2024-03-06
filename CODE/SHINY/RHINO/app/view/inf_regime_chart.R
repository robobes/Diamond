box::use(
  echarts4r,
  shiny[h3, moduleServer, NS, tagList,renderPlot,plotOutput],
  readr,
  dplyr,
  ggplot2
)


dat <- readr$read_csv("~/Github/Diamond/DATA/SHINY/regime_data.csv")
plotdat <- dat |> dplyr$filter(Field =="INF_YOY",Country=="US") |>  dplyr$rename("Date"=...1)

#' @export
ui <- function(id) {
  ns <- NS(id)
  tagList(
    h3("Chart"),
    plotOutput(ns("inf_regime_chart"))
  )
  
}

#' @export
server <- function(id) {
  moduleServer(id, function(input, output, session) {
    output$inf_regime_chart <- renderPlot(
      ggplot2$ggplot(plotdat, ggplot2$aes(x = Date, y = Value)) +
        ggplot2$geom_rect(ggplot2$aes(xmin = dplyr$lag(Date), xmax = Date, ymin = -Inf, ymax = Inf, fill = Regime, alpha = 0.002)) +
        ggplot2$geom_hline(ggplot2$aes(yintercept=0),col="maroon4")+
        ggplot2$geom_line() +
        ggplot2$scale_fill_manual(values = c("DISINFLATION" = "darkolivegreen3", "FIRE" = "firebrick3","ICE"="lightsteelblue3",
                                     "REFLATION"="navajowhite"))+
        ggplot2$labs(x = "Date", y = "Value", title = "Value Over Time by Regime") +
        ggplot2$theme(panel.grid.major = ggplot2$element_blank(), panel.grid.minor = ggplot2$element_blank(),
              panel.background = ggplot2$element_blank())+
        ggplot2$guides(alpha = FALSE,colour=FALSE) 
    )
      
    print("Chart module server part works!")
  })
}