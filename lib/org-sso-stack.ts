import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as customSso from "./constructs/sso";
import * as identitystore from "aws-cdk-lib/aws-identitystore";
import * as sso from "aws-cdk-lib/aws-sso";
import * as iam from "aws-cdk-lib/aws-iam";
import { orgConfig } from "./org-config";

customSso.config(orgConfig.sso);

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

    // The custom construct I wrote supports a handful of properties supported
    // by AWS SSO, but it'd be easy to extend if you need the others. 
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

    // the native SSO "CfnAssignment" extended by the construct below allows only
    // one account-group-permissionet mapping per resource, but you could write a 
    // a custom construct to (for example) accept an array of permission sets and/or account IDs
    // and create an assignment for each combination. 
    new customSso.SsoGroupAssignment(this,`SsoGroupAssignment_ReadOnlyGroup`,{
      ssoGroup: readOnlySsoGroup,
      ssoPermissionSet: readOnlySsoPermissionSet,
      accountId: orgConfig.accounts.sandbox,
    });
  }
}
