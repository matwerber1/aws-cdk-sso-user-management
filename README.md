# AWS CDK SSO Stack

This is an example AWS CDK stack in Python that demonstrates the management of AWS SSO users, groups, permission sets, and account assignments entirely within the CDK.

I have an early first-attempt in Typescript available in the `typescript-old` branch of this repo, though I think the 2nd pass in Python in this `main` branch is a better overall solution.

## Key features

- **Support for AWS SSO Users** Custom CloudFormation Resource for creating, updating, and deleting AWS SSO users (as of this writing, CloudFormation doesn't offer native support; the AWS SSO create-user/update-user SDK/CLI commands aren't well-documented, so this is a big time saver)

  - I've only added support for username, first name, last name, and email
  - only supports SSO when AWS Identity Center is acting as your identity provider. I imagine that solution would also work with little to no modification if you're using an external identity provider without SCIM, but I'm not sure.

- **Support for AWS SSO groups, users, and permission sets created outide of this CDK app** - very handy when, for example, you have existing SSO groups and permission sets created by AWS Control Tower

- **Helper methods** for 1/ adding a list of users to a group and 2/ assigning a given SSO group and permission set combination a list of accounts.

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
