class WeatherIngestion:
    def __init__(self, database, client, locations):
        self.database = database
        self.client = client
        self.locations = locations
