class OWM:
    def __init__(self, *args, **kwargs):
        pass

    class WeatherManager:
        def weather_at_coords(self, lat, lon):
            class Dummy:
                def __init__(self):
                    self.location = type('L', (), {'name': 'Loc'})
                    self.weather = type('W', (), {
                        'temperature': lambda self, unit: {'temp': 70},
                        'detailed_status': 'Clear',
                        'status': 'Clear',
                        'weather_icon_name': '01d'
                    })()
            return Dummy()

    def weather_manager(self):
        return self.WeatherManager()


class commons:
    class exceptions:
        class UnauthorizedError(Exception):
            pass
