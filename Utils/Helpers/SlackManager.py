import pytz
from datetime import datetime
from Utils.config import slack_client
from slack_sdk.errors import SlackApiError


class SlackManager:
    def __init__(self):
        self.client = slack_client
        self.channel = "C07FK8DJLJC"
        self.timezone = pytz.timezone("Asia/Kolkata")
        self.dashboard_url = "https://admin.sukoonunlimited.com/admin/experts/"

    def join_channel(self):
        try:
            response = self.client.conversations_join(channel=self.channel)
            print("Joined channel:", response)
        except SlackApiError as e:
            print(f"Error joining channel: {e}")

    def compose_message(self, status: bool, expert_name: str, expert_id: str):
        details_block = {
            "type": 'section',
            "text": {
                "type": 'mrkdwn',
                "text": '*Details:*',
            },
        }
        actions_block = {
            "type": 'actions',
            "elements": [
                {
                    "type": 'button',
                    "text": {
                        "type": 'plain_text',
                        "text": 'Check Sarathi Timings',
                    },
                    "value": 'expert_timings',
                    "url": f"{self.dashboard_url}{expert_id}#timings",
                    "action_id": 'button_expert_timings',
                },
            ],
        }

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{expert_name}* is now *{'online' if status else 'offline'}*. {'🎉' if status else '🚫'}"
                }
            },
            details_block,
            {
                "type": 'section',
                "fields": [
                    {
                        "type": 'mrkdwn',
                        "text": f'*Time:*\n{datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")}'
                    },
                    {
                        "type": 'mrkdwn',
                        "text": f'*Status:*\n{"Online" if status else "Offline"}'
                    }
                ]
            },
            actions_block
        ]
        return blocks

    def send_message(self, status: bool, expert_name: str, expert_id: str):
        message = self.compose_message(status, expert_name, expert_id)
        try:
            self.join_channel()
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=message,
                text=f"{expert_name} is now {
                    'online' if status else 'offline'}"
            )
            return response
        except SlackApiError as e:
            print(f"Error: {e}")
            return e.response["error"]
