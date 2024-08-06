from Utils.Constants.gqlQueries import listEventsQuery
from Utils.Services.GQLClient import call_graphql

class ListEvents:
    def __init__(self, limit: int = 500):
        self.limit = limit
        self.query = listEventsQuery

    def get_events(self):
        params = {"limit": self.limit}
        return call_graphql(self.query, params, message="get_events")
        