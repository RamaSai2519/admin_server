from bson import ObjectId
from datetime import timedelta
from flask import request, jsonify
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import userwebhookmessages_collection, users_collection, wafeedback_collection


class WAService:
    @staticmethod
    def get_wa_history():
        if request.method == "GET":
            size = request.args.get('size', '10')
            if size == "all":
                offset = 0
                size = "all"
                page = 1
            else:
                size, offset, page = uf.pagination_helper()

            if size != "all":
                userwebhookmessages = list(userwebhookmessages_collection.find(
                    {"body": {"$ne": None}}
                ).sort("createdAt", -1).skip(int(offset)).limit(int(size)))
            else:
                userwebhookmessages = list(userwebhookmessages_collection.find(
                    {"body": {"$ne": None}}
                ).sort("createdAt", -1))

            total_messages = userwebhookmessages_collection.count_documents(
                {"body": {"$ne": None}}
            )

            for message in userwebhookmessages:
                message["_id"] = str(message["_id"])
                message["userId"] = str(message["userId"])
                message["createdAt"] = (message["createdAt"] + timedelta(
                    hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                user = users_collection.find_one(
                    {"_id": ObjectId(message["userId"])})
                if user:
                    message["userName"] = user["name"] if "name" in user else ""
                    message["userNumber"] = user["phoneNumber"] if "phoneNumber" in user else ""
                else:
                    message["userName"] = ""
                    message["userNumber"] = ""
            return jsonify({
                "data": userwebhookmessages,
                "total": total_messages,
                "page": page,
                "pageSize": size
            })
        else:
            return jsonify({"error": "Invalid request method"}), 404

    @ staticmethod
    def get_feedbacks():
        size = request.args.get('size', '10')
        page = request.args.get('page', '1')

        try:
            size = int(size)
            page = int(page)
            offset = (page - 1) * size
        except ValueError:
            offset = 0
            size = "all"

        if size != "all":
            feedbacks = list(wafeedback_collection.find({}).sort(
                "createdAt", -1).skip(offset).limit(size))
        else:
            feedbacks = list(wafeedback_collection.find(
                {}).sort("createdAt", -1))

        total_feedbacks = wafeedback_collection.count_documents({})

        for feedback in feedbacks:
            feedback["_id"] = str(feedback["_id"])
            feedback["createdAt"] = (feedback["createdAt"] + timedelta(
                hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            feedback["userName"] = hf.get_user_name(
                ObjectId(feedback["userId"]))
            feedback["expertName"] = hf.get_expert_name(
                ObjectId(feedback["sarathiId"]))
            feedback["body"] = feedback["body"][2:]
            feedback["body"] = str(feedback["body"]).replace("_", " ")

        return jsonify({
            "data": feedbacks, "total": total_feedbacks,
            "page": page, "pageSize": size
        })
