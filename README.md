# AWS CDK SSO User Management Example

This repo contains a lightweight example custom CloudFormation resource that uses AWS identitystore APIs to create, update, and delete SSO users.

This project assumes you've already set up AWS SSO with IAM Identity Center and that IAM identity center is acting as your identity provider (IdP).

## Quick start

1. Install dependencies: `npm install`

2. Add configuration to `./lib/org-config.template.ts`:

   * `identityStoreId` and `instanceArn` available using AWS CLI for your organization management account: `aws sso-admin list-instances | jq '.Instances[0]'`

   * SSO allows string usernames. If you want usernames to be email addresses, set `requireUsernameAsEmail: true`. If you require email addresses, use `allowedEmailDomains: []` to specify which domains they can come from. This will only be enforced when using the custom construct in this project. It won't stop an admin from creating users with whatever email or domain they want outside of the CDK.

   * `region` is the region in your management account where SSO has been set up. 

   * populate the `accounts: {}` object with entries of `accountName: "<account_id>"`. The account name is arbitrary and just used as shorthand in this project; it does not need to match the actual account name configured in AWS.

3. rename `org-config.template.ts` to `org-config.ts`. Note - this file will be ignored in .gitignore to avoid committing within this demo project. If you use or adapt this in a private repo, you'd want to commit the file.

4. Edit `./bin/app.template.ts` to deploy to your management account and region you've selected for AWS SSO and rename to `./bin/app.ts` (same note about gitignore as above):

    ```sh
    new SsoConfigurationStack(app, "SsoStack", {
    env: {
        account: "<YOUR MANAGEMENT ACCOUNT ID>",
        region: "<YOUR REGION WHERE AWS SSO / IDENTITY CENTER CREATED>",
    },
    stackName: "cdk-organization-sso",
    });
    ```

5. Edit `./lib/org-sso-stack.ts` to your heart's content. Here's an example:

    ```ts
    export class SsoConfigurationStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        cdk.Tags.of(scope).add("cdk-project", "demo of user management with SSO");

        const readOnlySsoGroup = new identitystore.CfnGroup(
        this,
        "ReadOnlySsoGroup",
        {
            displayName: "Read-only",
            description: "Read-only group for demo CDK project",
            identityStoreId: orgConfig.sso.identityStoreId,
        },
        );

        const readOnlySsoPermissionSet = new sso.CfnPermissionSet(
        this,
        "ReadOnlySsoPermissionSet",
        {
            instanceArn: orgConfig.sso.instanceArn,
            name: "ReadOnlyAccess",
            description: "Demo permission set for read-only access",
            inlinePolicy: new iam.PolicyDocument({
            statements: [
                new iam.PolicyStatement({
                effect: iam.Effect.ALLOW,
                actions: ["ec2:List*", "ecy2:Describe*"],
                resources: ["*"],
                }),
            ],
            }),
            sessionDuration: "PT1H", // ISO-8601 format
        },
        );

        new customSso.SsoUser(this, "SsoUserForSomeUser", {
        retainUserIfStackDeleted: false,
        userAttributes: {
            userName: "someuser@example.com",
            firstName: "Jane",
            lastName: "Smith",
            title: "Engineer",
        },
        groups: [readOnlySsoGroup],
        });

        new customSso.SsoGroupAssignment(this,`SsoGroupAssignment_ReadOnlyGroup`,{
        ssoGroup: readOnlySsoGroup,
        ssoPermissionSet: readOnlySsoPermissionSet,
        accountId: orgConfig.accounts.sandbox,
        });
    }
    }
    ```

6. Deploy your project: `cdk deploy`

7. When you first deploy your project, `cdk.json` will be created with context about your environment. This file is in .gitignore because this is a demo project. Remember to add and commit `cdk.json` in a real project (should not be committed in public repos).
