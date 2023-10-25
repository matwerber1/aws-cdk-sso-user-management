import os
from typing import Optional, Union, Sequence, Dict, Any

from aws_cdk import IResolvable
from aws_cdk.aws_sso import CfnAssignment, CfnPermissionSet
from constructs import Construct

from ..config import SsoConfig
from .sso_group import SsoGroup
from .sso_user import SsoUser

dirname = os.path.dirname(__file__)


class SsoPermissionSet(Construct):
    def __init__(self, scope: Construct, *,
        name: str,
        customer_managed_policy_references: Optional[Union[IResolvable, Sequence[Union[IResolvable, Union[CfnPermissionSet.CustomerManagedPolicyReferenceProperty, Dict[str, Any]]]]]] = None,
        description: Optional[str] = None,
        inline_policy: Any = None,
        managed_policies: Optional[Sequence[str]] = None,
        permissions_boundary: Optional[Union[IResolvable, Union[CfnPermissionSet.PermissionsBoundaryProperty, Dict[str, Any]]]] = None,
        relay_state_type: Optional[str] = None,
        session_duration: Optional[str] = None,
    ):
        """
        Instantiate a new permission set. If a permission set already exists and you just
        want to use that, use the SsoPermissionSet.from_existing_permission_set() class method
        """
        id = "SsoPermissionSet_" + name
        super().__init__(scope, id)

        permission_set = CfnPermissionSet(self, id=id,
            name=name, instance_arn=SsoConfig.instance_arn.value,
            customer_managed_policy_references=customer_managed_policy_references,
            description=description,
            inline_policy=inline_policy,
            managed_policies=managed_policies,
            permissions_boundary=permissions_boundary,
            relay_state_type=relay_state_type,
            session_duration=session_duration
        )
        self.permission_set_name = name
        self.permission_set_arn = permission_set.attr_permission_set_arn

    @classmethod
    def from_existing_permission_set(
        cls, scope: Construct, *, permission_set_name: str, permission_set_arn: str
    ):
        """
        Use when you want to reference a Permission Set created outside of this CDK project.
        Not required, but convenient as the SsoPermissionSet class let's you use a new or existing
        permission set in the same places downstream, if needed.
        """
        # The __new__ is a special method to create an instance without calling the class constructor,
        # since that would result in us trying to create a new permission set when we just want to
        # reference an existing one.
        id = "SsoPermissionSet_" + permission_set_name
        instance = super(SsoPermissionSet, cls).__new__(cls)
        super(SsoPermissionSet, instance).__init__(scope, id)
        instance.permission_set_name = permission_set_name
        instance.permission_set_arn = permission_set_arn
        return instance

    def grant_to_group_for_account(self, group: SsoGroup, account_id: str):
        """
        Allow members of the provided group to use this permission set for given account ID.
        """
        CfnAssignment(
            self,
            id="Assign_"
            + self.permission_set_name
            + "_toGroup_"
            + group.group_name
            + "_for_"
            + account_id,
            instance_arn=SsoConfig.instance_arn.value,
            permission_set_arn=self.permission_set_arn,
            principal_id=group.group_id,
            principal_type="GROUP",
            target_id=account_id,
            target_type="AWS_ACCOUNT",
        )

    # def grantToGroupForAccounts(self, group: SsoGroup, account_ids: list[str]):
    #     """
    #     Allow members of the provided group to use this permission set for one or more account IDs.
    #     """
    #     for account_id in account_ids:
    #         self.grantToUserForAccount(group, account_id)

    def grant_to_user_for_account(self, user: SsoUser, account_id: str):
        """
        Assign a permission set to a specific user for a specific account.
        Best practice is to use group-based access over individual user assignments.
        """
        CfnAssignment(
            self,
            id="Assign_"
            + self.permission_set_name
            + "_toUser_"
            + user.username
            + "_for_"
            + account_id,
            instance_arn=SsoConfig.instance_arn.value,
            permission_set_arn=self.permission_set_arn,
            principal_id=user.user_id,
            principal_type="USER",
            target_id=account_id,
            target_type="AWS_ACCOUNT",
        )

    def grant_to_user_for_accounts(self, user: SsoUser, account_ids: list[str]):
        for account_id in account_ids:
            self.grant_to_user_for_account(user, account_id)