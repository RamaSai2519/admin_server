from flask_restful import Resource
from Utils.models.get_events.main import ListEvents

class EventsService(Resource):

    def get(self):
        output = ListEvents().get_events()
        return output
    