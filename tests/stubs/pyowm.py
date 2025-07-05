class UnauthorizedError(Exception):
    pass

class Weather:
    def __init__(self):
        self._temp = 70
        self.detailed_status = 'Clear'
        self.status = 'Clear'
        self.weather_icon_name = '01d'

    def temperature(self, unit):
        return {'temp': self._temp}

class Observation:
    def __init__(self):
        self.location = type('loc', (), {'name': 'Test'})()
        self.weather = Weather()

class WeatherManager:
    def weather_at_coords(self, lat, lon):
        return Observation()

class OWM:
    def __init__(self, api_key):
        self.api_key = api_key

    def weather_manager(self):
        return WeatherManager()

class commons:
    class exceptions:
        UnauthorizedError = UnauthorizedError
