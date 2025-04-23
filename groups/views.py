from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from groups.models import ExpenseGroup, GroupMembership
from .serializers import AddUserToGroupSerializer, CreateGroupSerializer, GroupInfoSerializer, GroupMemberSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

User = get_user_model()

class GroupMembersView(generics.ListAPIView):
    """
    View to list all members of a group.
    """
    serializer_class = GroupMemberSerializer  # Replace with your serializer class
    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        uuid = self.kwargs.get('uuid')
        if group_id or uuid:
            if group_id:
                group = ExpenseGroup.objects.filter(
                    id=group_id,
                ).prefetch_related('members').first()
            else:
                group = ExpenseGroup.objects.filter(
                    uuid=uuid,
                ).prefetch_related('members').first()

            if not group:
                raise PermissionDenied("Group not found.")

            # Check if the user is a member of the group
            if self.request.user not in group.members.all():
                raise PermissionDenied("You are not a member of this group.")
            
            return ExpenseGroup.objects.filter(id=group.id)
        return ExpenseGroup.objects.filter(members=self.request.user)
    

class CreateGroupView(generics.CreateAPIView):
    """
    API view to create a new group.
    """
    serializer_class = CreateGroupSerializer

class AddUserToGroupView(APIView):
    """
    API view to add a user to a group.
    """

    def post(self, request, uuid):
        group = get_object_or_404(ExpenseGroup, uuid=uuid)
        if not group:
            return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)
        if GroupMembership.objects.filter(user=request.user, group=group).exists():
            return Response({'error': 'You are already a member of this group.','id':group.id}, status=status.HTTP_200_OK)
        GroupMembership.objects.create(user=request.user, group=group)

        return Response({'message': f'User {request.user.username} added to group {group.name}.', 'id':group.id}, status=status.HTTP_200_OK)

class GroupAll(APIView):
    """
    API view to list all groups.
    """
    serializer_class = GroupInfoSerializer
    permission_classes = [AllowAny,]


    def get(self, request, uuid=None):
        # uuid = request.query_params.get('uuid')
        if uuid:
            groups = ExpenseGroup.objects.get(
                uuid=uuid,
            )
            serializer = self.serializer_class(groups, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({"error": "UUID not provided."}, status=status.HTTP_400_BAD_REQUEST)
