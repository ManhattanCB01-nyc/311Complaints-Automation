the github repository has 2 python files and an yml file 

the first yml file has the action : the action to run the big query code daily,
we run the bigquery code daily because we are updating 311 dashboard daily .
in order to update 311 dashboard daily we need to update the data from open nyc datset https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9/about_data
it does the action daily.

**the bigquery.ipynb helps us to run a python file which updates the file in bigquery and the drive .**

**ggplot also does a lot of wok:**

It prevents downloading years of duplicate data (Incremental Loading): The NYC 311 database is massive. If the script didn't know when it last ran, it would have to download all the data from July 2018 up to today every single time it executes.

It keeps you from getting blocked by the API: The NYC Open Data API (like almost all web APIs) has rate limits. If you ask it to send you millions of historical rows every single day, it will quickly throttle your connection or block you entirely for stressing their servers.

It acts as a fail-safe for crashes: If the script breaks halfway through—maybe the internet drops, or the NYC API goes down—the progress file won't get updated. The next time the script runs, it will look at the old date and simply try again, ensuring no data falls through the cracks.
