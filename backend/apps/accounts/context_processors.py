from .models import UserNotification


def unread_messages_processor(request):
    if not request.user.is_authenticated:
        return {"has_unread_messages": False}

    has_unread = UserNotification.objects.filter(
        user_id=request.user.id, is_read=False
    ).exists()
    return {"has_unread_messages": has_unread}
