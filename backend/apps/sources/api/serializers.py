from rest_framework import serializers

from apps.sources.models import Source


class SourceSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="get_platform_display")

    class Meta:
        model = Source
        fields = ["id", "platform", "identifier", "topic_id", "last_parsed_id"]
