import {
  CloudFormationCustomResourceCreateEvent,
  CloudFormationCustomResourceUpdateEvent,
} from "aws-lambda";

/** Contains configuration values that are passed to individual custom constructs */
export interface SsoConfigProps {
  identityStoreId: string;
  requireUsernameAsEmail: boolean;
  allowedEmailDomains: string[];
  instanceArn: string;
  region: string;
}

/** Properties of the SSO user that are used to create the user in the IdentityStore.  */
export type SsoUserAttributes = {
  userName: string;
  firstName: string;
  lastName: string;
  middleName?: string;
  title?: string;
  email?: string;
  phoneNumber?: string;
  userType?: string;
};

/** The attributes passed to the Lambda function responsible for creating an SSO user */
export type CloudFormationSsoUserResourceProperties = {
  identityStoreId: string;
  userAttributes: SsoUserAttributes;
  retainUserIfStackDeleted: boolean;
};

export type SsoUserCreateEvent = {
  ResourceProperties: CloudFormationSsoUserResourceProperties;
} & Omit<CloudFormationCustomResourceCreateEvent, "ResourceProperties">;

export type SsoUserUpdateEvent = {
  ResourceProperties: CloudFormationSsoUserResourceProperties;
  OldResourceProperties: CloudFormationSsoUserResourceProperties;
} & Omit<
  CloudFormationCustomResourceUpdateEvent,
  "ResourceProperties" | "OldResourceProperties"
>;
