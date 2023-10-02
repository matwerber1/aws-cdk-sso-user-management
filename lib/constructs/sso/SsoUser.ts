import { Construct } from "constructs";
import * as cdk from "aws-cdk-lib";
import * as cr from "aws-cdk-lib/custom-resources";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambdaNode from "aws-cdk-lib/aws-lambda-nodejs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as identitystore from "aws-cdk-lib/aws-identitystore";
import * as path from "path";
import { SsoUserAttributes, SsoConfigProps } from "./types";

export interface SsoUserConstructorProps {
  /** If resource is removed from stack or stack is deleted, should SSO User be retained?
   *  Default: `true` */
  retainUserIfStackDeleted: boolean;
  userAttributes: SsoUserAttributes;
  groups?: identitystore.CfnGroup[];
}

/** Custom resource to create an AWS SSO User using AWS Identity Store APIs via a
 *  Lambda function that acts as a custom CloudFormation resource handler. */
export class SsoUser extends Construct {
  private static lambdaEventHandler: lambdaNode.NodejsFunction;
  private static CustomResourceProvider: cr.Provider;
  private static ssoConfig: SsoConfigProps;
  private readonly props: SsoUserConstructorProps;
  private readonly ssoUserCdkCustomResource: cdk.CustomResource;
  readonly groups: identitystore.CfnGroup[];

  constructor(scope: Construct, id: string, props: SsoUserConstructorProps) {
    super(scope, id);
    if (!SsoUser.ssoConfig) {
      throw new Error(
        `SsoUser.config() must be called before creating a user.`,
      );
    }
    this.props = props;
    this.validateUsernameType();
    this.validateUsernameFromApprovedDomain();
    this.ssoUserCdkCustomResource = this.createSsoUser();
    this.addUserToGroups();
  }

  static config(props: SsoConfigProps) {
    SsoUser.ssoConfig = props;
  }

  private createSsoUser() {
    this.setOrCreateCustomResourceProvider();
    return new cdk.CustomResource(this, "CustomUserResource", {
      resourceType: "Custom::SsoUser",
      properties: {
        userAttributes: this.props.userAttributes,
        identityStoreId: SsoUser.ssoConfig.identityStoreId,
        retainUserIfStackDeleted: this.props.retainUserIfStackDeleted,
      },
      serviceToken: SsoUser.CustomResourceProvider.serviceToken,
    });
  }

  private addUserToGroups() {
    const groups = this.props.groups || [];
    for (const [index, group] of groups.entries()) {
      new identitystore.CfnGroupMembership(
        this,
        `GroupMembership_${index.toString()}`,
        {
          identityStoreId: SsoUser.ssoConfig.identityStoreId,
          groupId: group.attrGroupId,
          memberId: {
            userId: this.ssoUserCdkCustomResource.getAtt("UserId").toString(),
          },
        },
      );
    }
  }

  private validateUsernameType() {
    const username = this.props.userAttributes.userName;
    if (SsoUser.ssoConfig.requireUsernameAsEmail) {
      if (!this.isEmail(username)) {
        throw new Error(`Username must be an email address.`);
      }
    }
  }

  private validateUsernameFromApprovedDomain() {
    const username = this.props.userAttributes.userName;
    const allowedEmailDomains = SsoUser.ssoConfig.allowedEmailDomains;
    if (this.isEmail(username) && allowedEmailDomains) {
      const usernameEmailDomain = getEmailDomain(username);
      if (!allowedEmailDomains.includes(usernameEmailDomain)) {
        throw Error(
          `Username must be an email address from one of the following domains: ${allowedEmailDomains.join(
            ", ",
          )}.`,
        );
      }
    }
  }

  /** See https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html **/
  private setOrCreateCustomResourceProvider() {
    // the getOrCreate approach ensures that CDK does not create a new Lambda function for each SsoUser instance
    if (!SsoUser.lambdaEventHandler) {
      SsoUser.lambdaEventHandler = new lambdaNode.NodejsFunction(
        this,
        "SsoUserEventHandler",
        {
          entry: path.join(__dirname, "SsoUser.lambda.ts"),
          handler: "handler",
          runtime: lambda.Runtime.NODEJS_18_X,
          logRetention: logs.RetentionDays.ONE_YEAR,
          timeout: cdk.Duration.seconds(10),
          initialPolicy: [
            new iam.PolicyStatement({
              actions: [
                "identitystore:CreateUser",
                "identitystore:DeleteUser",
                "identitystore:UpdateUser",
              ],
              resources: ["*"],
            }),
          ],
          environment: {
            SSO_REGION: SsoUser.ssoConfig.region,
          },
        },
      );

      SsoUser.CustomResourceProvider = new cr.Provider(
        this,
        "CustomResourceProvider",
        {
          onEventHandler: SsoUser.lambdaEventHandler,
          logRetention: logs.RetentionDays.ONE_YEAR,
        },
      );
    }
  }

  private isEmail(email: string): boolean {
    const regex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return regex.test(email);
  }
}

function getEmailDomain(email: string): string {
  const parts = email.split("@");
  if (parts.length !== 2) {
    throw new Error(`Email ${email} is not valid.`);
  }
  return parts[1];
}
