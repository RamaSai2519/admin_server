listScheduledJobsQuery = """
            query MyQuery($limit: Int = 500) {
                listScheduledJobs(limit: $limit) {
                    nextToken
                    items {
                        id
                        requestMeta
                        scheduledJobTime
                        scheduledJobStatus
                    }
                }
            }
            """

listEventsQuery = """
    query ListEvents($limit: Int) {
        listEvents(limit: $limit) {
            nextToken
            items {
                mainTitle
                subTitle
                hostedBy
                updatedAt
                createdAt
            }
        }
    }
"""
