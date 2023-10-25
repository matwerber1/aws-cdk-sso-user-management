from typing import Any

from aws_cdk import Aspects, Stack, Tags
from aws_cdk import aws_iam as iam
from cdk_nag import AwsSolutionsChecks
from constructs import Construct

from . import AwsAccounts, SsoConfig
from .constructs import (
    SsoGroup,
    SsoPermissionSet,
    SsoUser,
    SsoUserAttributes
)


class SsoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Apply cdk-nag linting for (common) security best practices
        Aspects.of(self).add(AwsSolutionsChecks())

        # Auto-assign tags to all taggable resources created in this stack
        Tags.of(self).add(key="created-by-cdk", value="true")
        Tags.of(self).add(key="cdk-project-name", value="cdk-sso")

        user_foo = SsoUser(
            self,
            user_attributes=SsoUserAttributes(
                email="someuser1@",
                username="username",    # can be same as email, if you want
                first_name="Foo",
                last_name="Foo",
            ),
        )
        user_bar = SsoUser(
            self,
            user_attributes=SsoUserAttributes(
                email="someuser2@",
                username="username2",    # can be same as email, if you want
                first_name="Bar",
                last_name="Bar",
            ),
        )

        all_users = [user_foo, user_bar]

        # ========== AWS Control Tower Permission Sets =========#
        # If you're using AWS Control Tower, it will have created the permission sets
        # below for you. If you want to refer to them in this project, you can use the
        # "from_existing_permission_set()" method below. 
        #
        # If you're not using Control Tower or don't want to use the SSO
        #  resources it created, you can remove the imports below. 
        SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSOrganizationsFullAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",       # You will need to look up "xxxxxxxxxxxxxx" from IAM Identity Center/SSO
        )
        readonly_permissions = SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSReadOnlyAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )
        admin_permissions = SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSAdministratorAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )
        SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSPowerUserAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )
        SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSServiceCatalogEndUserAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )
        SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSServiceCatalogAdminFullAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )
        # ========== AWS Control Tower Groups =========#
        # Same comments as above. You don't need to import these values if you're
        # not using Control Tower or don't want to use them in this project
        ctt_account_factory_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSAccountFactory",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", # You need to look these up for your account's specific groups
        )
        ctt_audit_account_admin_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSAuditAccountAdmins",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_service_catalog_admin_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSServiceCatalogAdmins",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_security_audit_poweruser_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSSecurityAuditPowerUsers",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_log_archive_admin_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSLogArchiveAdmins",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_control_tower_admin_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSControlTowerAdmins",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_security_auditors_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSSecurityAuditors",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        ctt_log_archive_viewer_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSLogArchiveViewers",
            group_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        all_control_tower_default_groups = [
            ctt_account_factory_group,
            ctt_audit_account_admin_group,
            ctt_service_catalog_admin_group,
            ctt_security_audit_poweruser_group,
            ctt_log_archive_admin_group,
            ctt_control_tower_admin_group,
            ctt_security_auditors_group,
            ctt_log_archive_viewer_group,
        ]
        # ===== END OF CONTROL TOWER GROUPS & PERMISSION SETS =====#

        # Create a custom permission set. Wrapper around aws_sso.CfnPermissionSet
        demo_permission_set = SsoPermissionSet(
            self,
            name="DemoPermissionSet",
            description="demo permission set",
            inline_policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListAllMyBuckets"],
                        resources=["*"],
                    )
                ]
            ).to_string()
        )

        # Create a group
        demo_group = SsoGroup(
            self,
            group_name="Demo User Group",
            description="Admin and read-only role to sandbox account",
        )

        # add user(s) to a group
        demo_group.add_users(all_users)

        # add permission set to a group
        demo_permission_set.grant_to_group_for_account(demo_group, AwsAccounts.SANDBOX.value)