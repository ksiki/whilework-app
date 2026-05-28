from rest_framework import serializers

from apps.sources.models import Source, SourceTopic


class SourceTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceTopic
        fields = ["id", "topic_id", "last_parsed_id"]


class SourceSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="get_platform_display")
    topics = SourceTopicSerializer(source="active_topics", many=True, read_only=True)

    class Meta:
        model = Source
        fields = ["id", "platform", "identifier", "last_parsed_id", "topics"]
