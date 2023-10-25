import os
from typing import Any, cast

from aws_cdk.aws_identitystore import CfnGroup, CfnGroupMembership
from constructs import Construct

from .. import SsoConfig
from .sso_user import SsoUser

dirname = os.path.dirname(__file__)


class SsoGroup(Construct):
    """
    Creates new AWS SSO Group. To reference an existing group that was created outside
    of this CDK stack, use the SsoGroup.fromExistingGroup() method instead of directly
    calling this class constructor.
    """

    def __init__(
        self,
        scope: Construct,
        *,
        group_name: str,
        description: str,
        **kwargs: Any,
    ):
        id = "SsoGroup-" + group_name
        super().__init__(scope, id)
        group = CfnGroup(
            self,
            id=id,
            identity_store_id=SsoConfig.identity_store_id.value,
            description=description,
            display_name=group_name,
        )
        self.group_name = group_name  # provided by user
        self.group_id = (
            group.attr_group_id
        )  # token that will resolve to string when deployed

    @classmethod
    def from_existing_group(
        cls, scope: Construct, *, group_name: str, group_id: str
    ) -> "SsoGroup":
        """
        Create a class instance of SsoGroup for an existing group instead
        of creating a new group in CloudFormation.
        """
        id = "SsoGroup" + group_name
        instance = super(SsoGroup, cls).__new__(cls)
        super(SsoGroup, instance).__init__(scope, id)
        instance.group_name = group_name
        instance.group_id = group_id
        return cast("SsoGroup", instance)

    def add_user(self, user: SsoUser) -> None:
        """Add user (class=SsoUser) to this group."""
        CfnGroupMembership(
            self,
            id=f"GroupMember_{user.username}",
            group_id=self.group_id,
            identity_store_id=SsoConfig.identity_store_id.value,
            member_id=CfnGroupMembership.MemberIdProperty(user_id=user.user_id),
        )

    def add_users(self, users: list[SsoUser]) -> None:
        """Add multiple users (class=SsoUser) to this group"""
        for user in users:
            self.add_user(user)