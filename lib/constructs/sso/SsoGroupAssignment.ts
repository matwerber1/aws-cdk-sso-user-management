import { Construct } from "constructs";
import * as identitystore from "aws-cdk-lib/aws-identitystore";
import * as sso from "aws-cdk-lib/aws-sso";
import { SsoConfigProps } from "./types";

type SsoGroupId = string;
type SsoGroup = SsoGroupId | identitystore.CfnGroup;
type SsoPermissionSetArn = string;
type SsoPermissionSet = SsoPermissionSetArn | sso.CfnPermissionSet;

export interface SsoGroupAssignmentConstructor {
  /** Accepts either a string with an existing SSO Permission Set Arn or an instance of the CDK sso.CfnGroup class */
  ssoPermissionSet: SsoPermissionSet;
  /** Accepts either a string with an existing SSO Group ID or an instance of the CDK identityStore.CfnGroup class */
  ssoGroup: SsoGroup;
  /** the 12-digit AWS account ID */
  accountId: string;
}

/** Allow a specific SSO Group to use a specific SSO Permission Set on a specific AWS Account.
 *  This class is a wrapper around the CDK's CfnAssignment class to simplify the Assignment declaration.
 */
export class SsoGroupAssignment extends sso.CfnAssignment {
  private static ssoConfig: SsoConfigProps;
  constructor(
    scope: Construct,
    id: string,
    props: SsoGroupAssignmentConstructor,
  ) {
    if (!SsoGroupAssignment.ssoConfig) {
      throw new Error(
        `SsoGroupAssignment.config() must be called before creating an assignment.`,
      );
    }
    super(scope, id, {
      ...props,
      permissionSetArn: SsoGroupAssignment.getPermissionSetArn(
        props.ssoPermissionSet,
      ),
      instanceArn: SsoGroupAssignment.ssoConfig.instanceArn,
      principalId: SsoGroupAssignment.getPrincipalIdFromGroup(props.ssoGroup),
      principalType: "GROUP",
      targetId: props.accountId,
      targetType: "AWS_ACCOUNT",
    });
  }

  /** Must be called before calling the class constructor. You can call directly, or call the
   *  the config() function in ./index.ts to configure all of the custom SSO resource classes
   *  at once.
   */
  public static config(props: SsoConfigProps) {
    SsoGroupAssignment.ssoConfig = props;
  }

  private static getPrincipalIdFromGroup(group: SsoGroup) {
    if (typeof group === "string") {
      return group;
    }
    return group.getAtt("GroupId").toString();
  }

  private static getPermissionSetArn(permissionSet: SsoPermissionSet) {
    if (typeof permissionSet === "string") {
      return permissionSet;
    }
    return permissionSet.getAtt("PermissionSetArn").toString();
  }
}
