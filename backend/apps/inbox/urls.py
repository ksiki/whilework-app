from django.urls import path

from .views import ReceiveRawBatchView

app_name = "inbox"

urlpatterns = [
    path("batch/", ReceiveRawBatchView.as_view(), name="receive_batch"),
]
