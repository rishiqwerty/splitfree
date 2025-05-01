from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from auth_app.utils import log_activity
from auth_app.models import Activity
from expenses.serializers import ExpenseSummarySerializer, UserSerializer
from expenses.utils import get_expense_icon
from utils.gemini_api_call import generate_content
from .models import ExpenseGroup, GroupMembership


def get_group_activities(group_id):
    group = get_object_or_404(ExpenseGroup, id=group_id)
    content_type = ContentType.objects.get_for_model(ExpenseGroup)
    activities = Activity.objects.filter(content_type=content_type, object_id=group.id)
    return activities


class GroupMemberSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    logged_in_user = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    # members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = ExpenseGroup
        fields = [
            "id",
            "uuid",
            "name",
            "group_icon",
            "members",
            "simplify_debt",
            "created_by",
            "created_at",
            "logged_in_user",
        ]

    def get_logged_in_user(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user.first_name
        return None

    def get_created_by(self, obj):
        return obj.created_by.first_name if obj.created_by else None


class CreateGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new group.
    """

    user_selected_icon = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = ExpenseGroup
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "members",
            "created_at",
            "group_icon",
            "user_selected_icon",
        ]  # Include 'members' if you want to allow adding members during creation

    def create(self, validated_data):
        request_user = self.context["request"].user
        user_selected_icon = validated_data.pop("user_selected_icon", None)
        if user_selected_icon:
            validated_data["group_icon"] = get_expense_icon(
                validated_data["name"], validated_data["description"]
            )
        group = ExpenseGroup.objects.create(**validated_data)
        group.members.add(request_user)
        group.created_by = request_user  # Set the creator of the group
        group.save()
        log_activity(
            user=request_user,
            name="Group Created",
            description=f"Group '{group.name}' was created. by {request_user.username}",
            related_object=group,
        )
        return group


class AddUserToGroupSerializer(serializers.Serializer):
    user_id = serializers.ReadOnlyField()

    def validate(self, data):
        request = self.context.get("request")
        group = self.context.get("group")

        # Check if the user is already a member of the group
        if GroupMembership.objects.filter(user=request.user, group=group).exists():
            raise serializers.ValidationError("User is already a member of this group.")
        return data


class GroupInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving group information.
    """

    created_by = serializers.SerializerMethodField()
    already_member = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseGroup
        fields = [
            "id",
            "uuid",
            "already_member",
            "name",
            "description",
            "created_by",
            "created_at",
        ]  # Include 'members' if you want to allow adding members during creation

    def get_created_by(self, obj):
        return obj.created_by.first_name if obj.created_by else None

    def get_already_member(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return GroupMembership.objects.filter(user=request.user, group=obj).exists()
        return False


class GroupActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving group activity.
    """

    user = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ["user", "name", "description", "timestamp"]  # Adjust fields as needed


class GroupOverviewSerializer(serializers.Serializer):
    """
    Serializer for retrieving group overview.
    """

    ai_overview = serializers.SerializerMethodField()

    def get_ai_overview(self, obj):
        expense = ExpenseSummarySerializer(
            obj, context={"request": self.context["request"]}
        )
        ai_overview = generate_content(
            f"""Generate a one liner random summary for current
                                        month  using following json response also add one
                                       random money savings tip:  json:{expense.data} make sure curreny is rupees"""
        ).replace("\n", "")
        return ai_overview
