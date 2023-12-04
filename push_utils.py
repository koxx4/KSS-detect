from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage


def send_push_message(token, message, extra=None):
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        body=message,
                        data=extra,
                        sound="default",
                        priority="high",
                        channel_id="default"))
    except Exception as exc:
        # Handle any exceptions here
        print(f"Error sending push notification: {exc}")
        return None

    return response


def send_important_event_message(object_names: list[str], token: str):
    message = f'UWAGA: {", ".join(object_names)} - wykryto ważne zdarzenie!'
    send_push_message(token, message, extra={'event': 'important-event'})
