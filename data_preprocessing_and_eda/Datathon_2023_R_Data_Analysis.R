## Choose the working directory where you have the data:
getwd()

# Downloading data into the working directory:
outfit <- read.csv("datathon/datathon/dataset/outfit_data.csv", header = TRUE)
product  <- read.csv("datathon/datathon/dataset/product_data.csv", header = TRUE)

## Most of products are made for "Female":

table(product$des_sex, useNA = "ifany")
sum(table(product$des_sex, useNA = "ifany"))

nrow(product)

### There are only 19 Kids products in the dataset

table(product$des_age, useNA = "ifany") 

### There are more data in outfit than in product.

nrow(outfit) 
### This means that one product can be part of multiple outfits.

table(product$des_line, useNA = "ifany")

### The line "HOME" is the responsable for unisex products

HOME <- subset(product, des_line=="HOME")

### The line "SHE" is the responsible for "Adult" "Female" products 
SHE <- subset(product, des_line=="SHE") 

### The line "SHE" will be the focus of the analysis.

### Let's look at what outfit num. 2003 looks like:
Outfit_2003 <- outfit$cod_modelo_color[outfit$cod_outfit==2003]

Outfit_2003_files <- product$des_filename[product$cod_modelo_color %in% Outfit_2003]

Outfit_2003_data <- product[product$cod_modelo_color %in% Outfit_2003, ]

file.show(paste0("datathon/", Outfit_2003_files))

### We can see multiple objects, what attributes are similar in them?

### Let's see which attributes are determining factors,
### to decide if an item is compatible with an outfit or not.

### For this analysis, we will consider an attribute to be significant for an outfit
### if 50% or more of the items in the outfit share the same attribute value


### The function analize, looks at an outfit (based on code), and returns
### a vector of attributes that are significant
analize <- function(code){
  
  cod_mode <- outfit$cod_modelo_color[outfit$cod_outfit== code ]
  outfit_sub_data <-  product[product$cod_modelo_color %in% cod_mode, ]
  factor <- c()
  for(colum in colnames(outfit_sub_data)[2:12]){
    CON <- as.vector(sum(table(outfit_sub_data[[colum]]))*0.5 <= table(outfit_sub_data[[colum]])[which.max(table(outfit_sub_data[[colum]]))])
    if(CON){
      factor <- c(factor, colum)
    }
  }
  return(factor)
}

### For each outfit, we will apply the function analize.
### The resulting data is stored in a list called "analyzed_data2"
### You can load the results, that are stored in "Factores_Outfit_50.RData"

# analized_data2 <- list()
#  for(code in unique(outfit$cod_outfit)){
#  analized_data2[[code]] <- analize(code)
#  }
#  save(analized_data2, file="Factores_Outfit_50.RData")
load("Factores_Outfit_50.RData")

### Now, lets transform the list, into a dataframe, with rows being outfits
### and columns attributes, with 0 if they are not important and 1 if they are-

### The outfits (rows):
num_outfits <- length(unique(outfit$cod_outfit))

### Creating the initial dataframe full of zeros.
Factor_Per_Outfit2 <- data.frame(outfit = unique(outfit$cod_outfit),
                                cod_color_code=rep(0, num_outfits),
                                des_color_specification_esp =rep(0, num_outfits),
                                des_agrup_color_eng =rep(0, num_outfits),
                                des_sex =rep(0, num_outfits),
                                des_age =rep(0, num_outfits),
                                des_line =rep(0, num_outfits),
                                des_fabric=rep(0, num_outfits),
                                des_product_category=rep(0, num_outfits),
                                des_product_aggregated_family=rep(0, num_outfits),
                                des_product_family=rep(0, num_outfits),
                                des_product_type=rep(0, num_outfits))

### Going through the analized_data2 and adding the information into Facror_Per_Outfit2

for(i in 1:length(analized_data2)){
  factors_outfit_x <- analized_data2[[i]]
  j <- 1
  while(j<=length(factors_outfit_x)){
    Factor_Per_Outfit2[i, factors_outfit_x[j]] <- 1
    j <- j+1
  }
}

### Now, we can check which attributes are factors.
### First we need to decide which elements we will look at.
### If we look at outfits composed of too few or too many items, then the results
### may be biased. So we need to determine an interval of the number of items
### in an outfit, for which we will look at the data.

### The numbre of items in each outfit
num_elements_outfit <- as.data.frame(table(outfit$cod_outfit))


### You can analyze the data in excel or other programm like JMP,~
### to decied which distribution the data folows
# library("writexl")
# write_xlsx(num_elements_outfit,"Num_elements_outfit.xlsx")

### We can see that the data doesn't follow a Normal distribution
hist(num_elements_outfit$Freq)

### On the other hand, the Log of our data, looks uniform. Since we have
### discrete values and not continues, it isn't Lognormal but we can 
### aproximate it as one.
num_elements_outfit$Log_Freq <- log(num_elements_outfit$Freq)
hist(num_elements_outfit$Log_Freq)

### Then we can find a centered interval in which 95% of data lies,
### using mean +/- 2 sigma. Then we raise the values to the power of e
### To see the real intervals:

s <- sd(num_elements_outfit$Log_Freq)
exp(mean(num_elements_outfit$Log_Freq)-2*s)
exp(mean(num_elements_outfit$Log_Freq)+2*s)

### 95% of outfits have from 3.46 to 8.47 items
### Thus, we will analyze data of outfits that has from 3 to 9 items

Data_Analysis <- Factor_Per_Outfit2[ num_elements_outfit$Freq %in% 3:9,]

### Now, let's check which attributes are factors.
### We plan a hypotheisis test:
### H0 = The attribute is not a factor
### H1 = The attribute is a factor
### If H1 is true, we would expect to have 1s and 0s in the 
### Attribute column with equal chance.
### Thus this is a tipical prop.test to see if the 
### probability is different from 0.5

### Color descripiton (e.i. WHITE / BLACK): Is a Factor
table(Data_Analysis$des_agrup_color_eng)
prop.test(table(Data_Analysis$des_agrup_color_eng), p = 0.5, alternative = "less")


### Color code / spanish description: Is not a Factor
table(Data_Analysis$cod_color_code)
table(Data_Analysis$des_color_specification_esp)

prop.test(table(Data_Analysis$cod_color_code), p = 0.5, alternative = "less")
prop.test(table(Data_Analysis$des_color_specification_esp), p = 0.5, alternative = "less")


### Sex, Age and Line: Always a factor ("SHE" produces Female clothing, "HOME" unisex, etc.)
table(Data_Analysis$des_sex)
table(Data_Analysis$des_age)
table(Data_Analysis$des_line)

### Fabric: A factor that is more important than color
table(Data_Analysis$des_fabric)
prop.test(table(Data_Analysis$des_fabric), p = 0.5, alternative = "less")


### Looking at other attributes makes no sense statistically
table(Data_Analysis$des_product_type)

### We conclude that for the predictive model,
### we will look at the SHE line. The model should first chose 
### prioritize choosing the same fabric for all items in an outfit
### and then try to choose a similar color. However
### the color code is not as essential as the color description,
### so we can choose diferent shades of WHITE/BLACK