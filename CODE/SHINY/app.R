#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)

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
            selectInput("whichplot",label = "Plot: ",choices = c("Inflation"="plotdat_inf_us",
                                                                 "Growth"="plotdat_gro_us"))
        ),

        # Show a plot of the generated distribution
        mainPanel(
           plotOutput("distPlot"),
           plotOutput("scatterPlot")
        )
    )
)

# Define server logic required to draw a histogram
server <- function(input, output) {

  load("/srv/shiny-server/Data_for_shiny.RData")
  plotdat <- reactive(get(input$whichplot))
  
  output$distPlot <- renderPlot({
        

        
        ggplot(plotdat, aes(x = Date, y = Value)) +
          geom_rect(aes(xmin = lag(Date), xmax = Date, ymin = -Inf, ymax = Inf, fill = Regime, alpha = 0.002)) +
          geom_hline(aes(yintercept=0),col="maroon4")+
          geom_line() +
          scale_fill_manual(values = c("DISINFLATION" = "darkolivegreen3", "FIRE" = "firebrick3","ICE"="lightsteelblue3",
                                       "REFLATION"="navajowhite"))+
          labs(x = "Date", y = "Value", title = "Value Over Time by Regime") +
          theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
                panel.background = element_blank())+
          guides(alpha = FALSE,colour=FALSE)
    })
    
  output$scatterPlot <- renderPlot({
  
    plot(mydat$x[1:(input$bins*20)],
         mydat$y[1:(input$bins*20)])
    
    })
  
    
    
}

# Run the application 
shinyApp(ui = ui, server = server)
