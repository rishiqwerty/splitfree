from rest_framework import serializers

from auth.views import User
from expenses.serializers import UserSerializer
from .models import ExpenseGroup, GroupMembership


class GroupMemberSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    logged_in_user = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    # members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = ExpenseGroup
        fields = ['id','uuid', 'name', 'members','created_by', 'created_at', 'logged_in_user']

    def get_logged_in_user(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return request.user.first_name
        return None

    def get_created_by(self, obj):
        return obj.created_by.first_name if obj.created_by else None
class CreateGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new group.
    """
    class Meta:
        model = ExpenseGroup
        fields = ['id', 'uuid', 'name', 'description', 'members', 'created_at']  # Include 'members' if you want to allow adding members during creation

    def create(self, validated_data):
        request_user = self.context['request'].user

        group = ExpenseGroup.objects.create(**validated_data)
        group.members.add(request_user)
        group.created_by = request_user  # Set the creator of the group
        group.save()
        return group
    
class AddUserToGroupSerializer(serializers.Serializer):
    user_id = serializers.ReadOnlyField()
    def validate(self, data):
        request = self.context.get('request')
        group = self.context.get('group')

        # Check if the user is already a member of the group
        if GroupMembership.objects.filter(user=request.user, group=group).exists():
            raise serializers.ValidationError("User is already a member of this group.")
        print(data)
        return data

class GroupInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving group information.
    """
    created_by= serializers.SerializerMethodField()
    already_member = serializers.SerializerMethodField()
    class Meta:
        model = ExpenseGroup
        fields = ['id', 'uuid', 'already_member', 'name', 'description', 'created_by', 'created_at']  # Include 'members' if you want to allow adding members during creation
    def get_created_by(self, obj):
        return obj.created_by.first_name if obj.created_by else None
    
    def get_already_member(self, obj):
        request = self.context.get('request')
        print(request.user)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return GroupMembership.objects.filter(user=request.user, group=obj).exists()
        return False