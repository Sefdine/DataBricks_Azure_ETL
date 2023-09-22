# Databricks notebook source
# import pandas as pd
# import random
# from datetime import datetime, timedelta

# # Generate data for January 2023
# start_date = datetime(2023, 1, 1)
# end_date = datetime(2023, 1, 31)
# date_generated = [start_date + timedelta(days=x) for x in range(0, (end_date-start_date).days)]

# transport_types = ["Bus", "Train", "Tram", "Metro"]
# routes = ["Route_" + str(i) for i in range(1, 11)]
# stations = ["Station_" + str(i) for i in range(1, 21)]

# # Randomly select 5 days as extreme weather days
# extreme_weather_days = random.sample(date_generated, 5)

# data = []

# for date in date_generated:
#     for _ in range(32):  # 32 records per day to get a total of 992 records for January
#         transport = random.choice(transport_types)
#         route = random.choice(routes)

#         # Normal operating hours
#         departure_hour = random.randint(5, 22)
#         departure_minute = random.randint(0, 59)

#         # Introducing Unusual Operating Hours for buses
#         if transport == "Bus" and random.random() < 0.05:  # 5% chance
#             departure_hour = 3

#         departure_time = f"{departure_hour:02}:{departure_minute:02}"

#         # Normal duration
#         duration = random.randint(10, 120)

#         # Introducing Short Turnarounds
#         if random.random() < 0.05:  # 5% chance
#             duration = random.randint(1, 5)

#         # General delay
#         delay = random.randint(0, 15)

#         # Weather Impact
#         if date in extreme_weather_days:
#             # Increase delay by 10 to 60 minutes
#             delay += random.randint(10, 60)

#             # 10% chance to change the route
#             if random.random() < 0.10:
#                 route = random.choice(routes)

#         total_minutes = departure_minute + duration + delay
#         arrival_hour = departure_hour + total_minutes // 60
#         arrival_minute = total_minutes % 60
#         arrival_time = f"{arrival_hour:02}:{arrival_minute:02}"

#         passengers = random.randint(1, 100)
#         departure_station = random.choice(stations)
#         arrival_station = random.choice(stations)

#         data.append([date, transport, route, departure_time, arrival_time, passengers, departure_station, arrival_station, delay])

# df = pd.DataFrame(data, columns=["Date", "TransportType", "Route", "DepartureTime", "ArrivalTime", "Passengers", "DepartureStation", "ArrivalStation", "Delay"])
# df.to_csv("public_transport_data.csv", index=False)


# COMMAND ----------

# MAGIC %scala
# MAGIC var containerName = "publictransportdata"
# MAGIC var storageAccountName = "sefdinenassufblobcontain"
# MAGIC var sas = "?sv=2022-11-02&ss=b&srt=sco&sp=rwdlacyx&se=2023-09-22T18:59:37Z&st=2023-09-22T10:59:37Z&spr=https&sig=Dw8729WqHuaaolekXDEvNJNUMaAJ4U71xSSex5Z9LrI%3D"

# COMMAND ----------

# MAGIC %scala
# MAGIC var url = "wasbs://" + containerName + "@" + storageAccountName + ".blob.core.windows.net/"
# MAGIC var config = "fs.azure.sas." + containerName + "." + storageAccountName + ".blob.core.windows.net"

# COMMAND ----------

# MAGIC %scala
# MAGIC dbutils.fs.mount(
# MAGIC     source = url,
# MAGIC     mountPoint = "/mnt/staging",
# MAGIC     extraConfigs = Map(config -> sas)
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC # Transformation
# MAGIC

# COMMAND ----------

df = spark.read.csv("/mnt/staging/raw/public-transport-data-650c6707b7a50741400514.csv", header=True)


# COMMAND ----------


from pyspark.sql.functions import col, year, day, month, date_format, expr
from pyspark.sql.types import DateType, IntegerType, StringType, TimestampType

# Define a dictionary to map column names to their data types
column_types = {
    'Date': DateType(),
    'TransportType': StringType(),
    'Route': StringType(),
    'DepartureTime': TimestampType(),
    'ArrivalTime': TimestampType(),
    'Passengers': IntegerType(),
    'DepartureStation': StringType(),
    'ArrivalStation': StringType(),
    'Delay': IntegerType()
}

# Cast the columns to their respective data types
for col_name, col_type in column_types.items():
    df = df.withColumn(col_name, col(col_name).cast(col_type))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Date
# MAGIC Extraire le year, month et day of the month

# COMMAND ----------

df = df.withColumn('Year', year(df['Date']))
df = df.withColumn('Month', month(df['Date']))
df = df.withColumn('Day', day(df['Date']))

# COMMAND ----------

display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Durée de voyage
# MAGIC Soustraire l'heure de départ et l'heure d'arrivée

# COMMAND ----------

df = df.withColumn('CurrentDelay', expr("ArrivalTime - DepartureTime")).cast(IntegerType() / 1000)

# Convert times to format HH:mm
df = df.withColumn('DepartureTime', date_format(df['DepartureTime'], 'HH:mm'))
df = df.withColumn('ArrivalTime', date_format(df['ArrivalTime'], 'HH:mm'))

# COMMAND ----------

# MAGIC %md
# MAGIC ## RetardCategory
# MAGIC 'Pas de Retard', 'Retard Court' (1-10 minutes), 'Retard Moyen' (11-20 minutes) et 'Long Retard' (>20 minutes).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Analyse des Passagers
# MAGIC Identifier les heures de pointe et hors pointe en fonction du nombre de passagers.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Analyse des Itinéraires
# MAGIC Calculer le retard moyen, le nombre moyen de passagers et le nombre total de voyages pour chaque itinéraire.
