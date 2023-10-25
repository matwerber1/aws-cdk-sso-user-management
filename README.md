# AWS CDK SSO Stack

This is an example AWS CDK stack in Python that demonstrates the management of AWS SSO users, groups, permission sets, and account assignments entirely within the CDK. The big win is a custom resource for managing AWS SSO users, as those aren't yet natively supported by CloudFormation.

## What you get from this project

In a nutshell, easy(?) AWS SSO management with CDK.

```py
class SsoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_foo = SsoUser(
            self,
            user_attributes=SsoUserAttributes(
                email="someuser1@",
                username="username",
                first_name="Foo",
                last_name="Foo",
            ),
        )
        user_bar = SsoUser(
            self,
            user_attributes=SsoUserAttributes(
                email="someuser2@",
                username="username2",
                first_name="Bar",
                last_name="Bar",
            ),
        )

        all_users = [user_foo, user_bar]

        # Support for using existing perission sets
        SsoPermissionSet.from_existing_permission_set(
            self,
            permission_set_name="AWSOrganizationsFullAccess",
            permission_set_arn=f"{SsoConfig.instance_arn.value}/ps-xxxxxxxxxxxxxx",
        )

        # Create new permission sets
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

        # Support for using existing SSO groups
        ctt_account_factory_group = SsoGroup.from_existing_group(
            self,
            group_name="AWSAccountFactory",
            group_id="xxxx-xxxx-xxx-xxxx-xxxxxxxx",
        )

        # Create new groups
        demo_group = SsoGroup(
            self,
            group_name="Demo User Group",
            description="Users can list buckets in our sandbox account",
        )

        # add user(s) to a group
        demo_group.add_users(all_users)

        # add permission set to a group for a given account
        demo_permission_set.grant_to_group_for_account(demo_group, AwsAccounts.SANDBOX.value)
```

## Available constructs and methods

### SsoUser

Uses AWS `identitystore` APIs in a custom CloudFormation resource to create, update, and delete existing SSO users.

Within the Lambda function ([lambda_functions/sso_user/index.py](sso/constructs/lambda_functions/sso_user/index.py)) source code, you can further customize behavior using the following configuration variables:

- `ALLOW_CREATE_REQUEST_TO_IMPORT_EXISTING_USER [default=True]` - supports "importing" an existing SSO user by creating an instance of `SSOUser` with a username, first name, last name, and email address that is identical to an existing user.

- `ALLOW_DELETE_USERS [default=False]` - If an `SsoUser` declaration is removed or the stack is deleted, this value determines whether the SSO user will actually be deleted. Default value is `False` to err on the side of caution. Perhaps adding a per-user `retention_policy` setting to the SsoUser constructor properties and passing it's value to the Lambda function for each user would be better (it'd certainly be more in-line with typical CloudFormation & CDK)... but I opted for the current approach because - at least in my environment - there aren't many users, they should never be deleted (at least, not in any forseeable future), and I didn't want to risk an inadvertent mistake or stack deletion suddenly locking everyone out.

`RETURN_DELETE_SUCCESS_EVEN_IF_DELETE_NOT_ALLOWED [default=True]` - If an SsoUser is removed from a stack but `ALLOW_DELETE_USERS=False`, should we fail the stack update or allow it to proceed? Similar to above, maybe a better approach is to use a per-user `retention_policy` setting.

### SsoGroup

Creates a new instance of an SSO Group from `aws_cdk.aws_identitystore.CfnGroup`, or allows you to create an SsoGroup from an existing group with `from_existing_group()`.

Once you've created an SSOGroup, the following helper methods are available for the group:

- `add_user()` - a convenience wrapper around `aws_cdk.aws_identitystore.CfnGroupMembership` that adds a single `SsoUser` to the group's membership.

- `add_users()` - allows you to pass a list of `SsoUser` objects and adds each of them to the group.

### SsoPermissionSet

Creates a new instance of an SSO Permission Set from `aws_cdk.aws_identitystore.CfnPermissionSet`, or allows you to create an SsoPermissionSet from an existing group with `from_existing_group()`.

Once you've created an SsoPermissionSet, the following helper methods are available for the permission set:

- `grant_to_group_for_account()` - a convenience wrapper around `aws_cdk.aws_identitystore.CfnAssignment` that grants a single SsoGroup permission to use the SsoPermissionSet with a specific AWS account ID.

- `grant_to_user_for_account()` - a convenience wrapper around `aws_cdk.aws_identitystore.CfnAssignment` that grants a single SsoUser permission to use the SsoPermissionSet with a specific AWS account ID.

- `grant_to_user_for_accounts()` - accepts an SsoUser and list of AWS account IDs and gives the user permission to use the permission set for each of the accounts.

## Quickstart

1. Clone repo

2. Update [./sso/config.py](./sso/config.py) with the AWS Account ID of your AWS Organization and related SSO configuration info available from IAM Identity Center in your management account in the region where you've set up SSO. Optionally provide a list of AWS account IDs and nicknames that you want to use in this solution.

3. Update [./sso/sso_stack.py](./sso/sso_stack.py) to define the AWS SSO users, groups, permission sets, and assignments to your AWS accounts.

4. Follow the "Default CDK instructions" below, run `cdk deploy`, and - hopefully - enjoy the results :)

## Default CDK Instructions

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```sh
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```sh
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```sh
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```sh
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```sh
cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation

Enjoy!
