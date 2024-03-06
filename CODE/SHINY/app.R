#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(ggplot2)
library(plotly)

# Define UI for application that draws a histogram
ui <- fluidPage(

    # Application title
    titlePanel("My Shiny App"),

    # Sidebar with a slider input for number of bins 
    sidebarLayout(
        sidebarPanel(
            sliderInput("bins",
                        "Number of bins:",
                        min = 1,
                        max = 50,
                        value = 30),
            selectInput("whichplot",label = "Plot: ",choices = c("Inflation"="inf",
                                                                 "Growth"="gro"))
        ),

        # Show a plot of the generated distribution
        mainPanel(
           plotlyOutput("distPlot"),
           plotOutput("scatterPlot")
        )
    )
)

# Define server logic required to draw a histogram
server <- function(input, output) {
  load("~/Github/Diamond/DATA/SHINY/Data_for_shiny.RData")
  #load("/srv/shiny-server/Data_for_shiny.RData")
  plotdat <-reactive(get(paste0("plotdat_",input$whichplot,"_us")))
  colvalues <- reactive(get(paste0("colorpalette_",input$whichplot)))
  output$distPlot <- renderPlotly({
        p <- ggplot(plotdat(), aes(x = Date, y = Value)) +
          geom_tile(aes(x = Date, y = (max(Value)+min(Value))/2, height = max(Value)-min(Value),width=90, fill = Regime,color=Regime), alpha = 0.5) +
          geom_hline(aes(yintercept=0),col="maroon4")+
          geom_line() +
          scale_fill_manual(values = colvalues())+
          scale_color_manual(values = colvalues())+
          labs(x = "Date", y = "Value", title = "Value Over Time by Regime") +
          theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
                panel.background = element_blank())+
          guides(alpha = "none",colour="none")
        ggplotly(p)
    })
    
  output$scatterPlot <- renderPlot({
  
    plot(mydat$x[1:(input$bins*20)],
         mydat$y[1:(input$bins*20)])
    
    })
  
    
    
}

# Run the application 
shinyApp(ui = ui, server = server)
