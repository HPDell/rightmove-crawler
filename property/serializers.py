from rest_framework import serializers
from property.models import Property

class PropertySerializer(serializers.Serializer):
    """
    Serializeer for Property
    """
    id = serializers.IntegerField(read_only=True)
    rightmove_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    type_name = serializers.CharField()
    distance = serializers.FloatField()
    beds = serializers.IntegerField()
    baths = serializers.IntegerField()
    url = serializers.CharField()
    price_pcm = serializers.IntegerField()
    price_pw = serializers.IntegerField()
    available_date = serializers.DateField()
    deposit = serializers.IntegerField()
    furnished = serializers.BooleanField()

    def create(self, validated_data):
        return Property.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.rightmove_id = validated_data.get('rightmove_id', instance.rightmove_id)
        instance.title = validated_data.get('title', instance.title)
        instance.type_name = validated_data.get('type_name', instance.type_name)
        instance.distance = validated_data.get('distance', instance.distance)
        instance.beds = validated_data.get('beds', instance.beds)
        instance.baths = validated_data.get('baths', instance.baths)
        instance.url = validated_data.get('url', instance.url)
        instance.price_pcm = validated_data.get('price_pcm', instance.price_pcm)
        instance.price_pw = validated_data.get('price_pw', instance.price_pw)
        instance.available_date = validated_data.get('available_date', instance.available_date)
        instance.deposit = validated_data.get('deposit', instance.deposit)
        instance.furnished = validated_data.get('furnished', instance.furnished)
        instance.save()
        return instance
