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

        # Reference existing perission sets
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

        # Create new groups
        demo_group = SsoGroup(
            self,
            group_name="Demo User Group",
            description="Admin and read-only role to sandbox account",
        )

        # add user(s) to a group
        demo_group.add_users(all_users)

        # add permission set to a group for a given account
        demo_permission_set.grant_to_group_for_account(demo_group, AwsAccounts.SANDBOX.value)
```

## Key features

### Support for AWS SSO Users

This is the big win (for me, at least!). As of this writing, CloudFormation doesn't offer native support for creating, updating, or deleting SSO users. On top of that, I found their `aws identitystore update-user` CLI and SDK docs... lacking... it was painful figuring out some of the quirks, primarily with the update-user API. This solution provides a custom CDK resource in the form of a Lambda function that wraps up my lessons learned and lets you use infra-as-code for SSO users.

> **Notes:**
>
> - I've only added support for username, first name, last name, and email
> - only supports SSO when AWS Identity Center is acting as your identity provider. I imagine that solution would also work with little to no modification if you're using an external identity provider without SCIM, but I'm not sure.

### Support for existing AWS SSO resources

Solution supports using existing SSO groups and permission sets.

There's also support for "importing" an existing AWS SSO user (see the custom resource Lambda code's 'create_user' method to learn more).

### Helper methods to reduce repetitive work

The native CloudFormation resources and CDK constructs for adding users to groups or adding a group to multiple accounts is tedious, as each one of these user-group or group-account-permissionset combinations is its own CloudFormation/CDK resource. I added some helper methods to abstract a lot of this away.

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
