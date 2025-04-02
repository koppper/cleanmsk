from rest_framework import serializers
from .models import Advice, AdviceCategory

class AdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ["id", "description", "order", "created_at"]


class AdviceByCategorySerializer(serializers.ModelSerializer):
    advices = AdviceSerializer(many=True, read_only=True)

    class Meta:
        model = AdviceCategory
        fields = ["id", "name",  "image", "advices"]
