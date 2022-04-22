import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


#Reading data from excel
df_ = pd.read_excel("HAFTA_03/Ders Notları/online_retail_II.xlsx",
                    sheet_name="Year 2010-2011")

#Our data so big that why i am taking copy of my data
df = df_.copy()

#When we check our data we can see multiple invoice for 1 order.
df.head()

###############################################################
# Data Understanding
###############################################################
df.shape
#(541910, 8)
#Observational Unit: 541910
#Variable: 8

#I want to check my data if there is a outlier problem etc.
df.describe().T

#Checking number of unique product
df["StockCode"].nunique()

#Checking number of each products
df[["Description","StockCode"]].value_counts()

#Top 5 Saled products
sale_quantity = df.groupby(["Description"]).agg({"Quantity": "count"})
sale_quantity.sort_values("Quantity",ascending=False).reset_index().head()

###############################################################
# Data Preparation
###############################################################
#Checking if there is null values
df.isnull().values.any()
df.isnull().sum()

df.dropna(inplace=True)

#C returned product so i did not take them
df = df[~df["Invoice"].str.contains("C", na=False)]

#POST is postage cost so i deleted it is not a product
df = df[~df["StockCode"].str.contains("POST", na=False)]

#Quantity and Price can not be lower than 1
df = df[(df['Quantity'] > 0)]
df = df[(df['Price'] > 0)]

#There is no total prices in df so i created new feature named ‘TotalPrice’
df["TotalPrice"] = df["Quantity"] * df["Price"]

df.head()


###############################################################
# Calculating RFM Metrics
###############################################################
#('2011-12-09 12:50:00') customer's latest purchase date
df["InvoiceDate"].max()

#Taking RFM measurment date as 2 days after from latest purchase date
today_date = dt.datetime(2011, 12, 11)

#RFM metrics
rfm=df.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                     'Invoice': lambda num: num.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

#Giving proper name to columns
rfm.columns = ['recency', 'frequency', 'monetary']
rfm.head()

#Monetary should be bigger than 0
rfm = rfm[rfm["monetary"] > 0]


#Scoring RFM scores between 1-5

rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])

rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

rfm.head()

#RFM Score

rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                    rfm['frequency_score'].astype(str))

rfm.head()

#Segmentation of RFM scores
#Segment map
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}


rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)

rfm.head()

import matplotlib.pyplot as plt


plt.pie(rfm.segment.value_counts(),
        labels=rfm.segment.value_counts().index,
        autopct='%.0f%%',
        colors=mycolors)
plt.show()

rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

champions = rfm[rfm['segment'] == 'champions']
need_attention = rfm[rfm['segment'] == 'need_attention']
at_risk = rfm[rfm['segment'] == 'at_Risk']

champions[['recency','frequency','monetary']].agg(['mean', 'count'])
#We have 656 shampions.Averagely they made 12 times shopping in a week and spent 6685.80300
#We can call them and make them feel special and learn what makes them stay and spend.We should inform them about our
#new products also we can apply up-selling strategy.Upselling means getting a customer to purchase a more expensive version
#of something they have either already. They are heavy spender why wont buy expensive version ?Also we can make cross-sell
#strategy to make them purchase more.


need_attention[['recency','frequency','monetary']].agg(['mean', 'count'])
#We have 186 need_attention .Averagely they made 2 times shopping in a 52 days and spent 892.80559
#Making some campaign, special offer etc. can move them the loyal customer potantial loyalist etc. otherwise
#they can moce to other segment such as at rist and hibernating.We dont want it beacuse acquiring a new customer is anywhere
#from five to 25 times more expensive than retaining an existing one .

at_risk [['recency','frequency','monetary']].agg(['mean', 'count'])
#We have 595 customer at risk .Averagely they made 3 times shopping in a 153 days and spent 1083.74019
#At Risk Customers are our customers who purchased often and spent big amounts,but haven’t purchased recently.
#Bring them back with personalized reactivation campaigns, special offers and promotions etc. to reconnect them.

need_attention_df = pd.DataFrame()
need_attention_df["need_attention_id"] = rfm[rfm["segment"] == "need_attention"].index
need_attention_df.head()

need_attention_df.to_excel("need_attention.xlsx")