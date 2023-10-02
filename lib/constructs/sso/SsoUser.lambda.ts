import { CloudFormationCustomResourceDeleteEvent, Handler } from "aws-lambda";

import {
  IdentitystoreClient,
  UpdateUserCommandInput,
  CreateUserCommand,
  AttributeOperation,
  DeleteUserCommand,
  UpdateUserCommand,
  CreateUserCommandInput,
} from "@aws-sdk/client-identitystore";

import { DocumentType } from "@smithy/types";
import {
  SsoUserCreateEvent,
  SsoUserUpdateEvent,
  CloudFormationSsoUserResourceProperties,
} from "./types";

// Should be provided as part of Lambda env config
if (!process.env.SSO_REGION) {
  throw new Error("SSO_REGION is not defined in the environment variables.");
}

const identityStoreClient = new IdentitystoreClient({
  region: process.env.SSO_REGION,
});

type SsoUserDeleteEvent = CloudFormationCustomResourceDeleteEvent;

export type SsoUserEvent =
  | SsoUserCreateEvent
  | SsoUserUpdateEvent
  | SsoUserDeleteEvent;

type SsoUserEventResponse = {
  PhysicalResourceId: string;
  Data?: {
    [Key: string]: unknown;
  };
  NoEcho?: boolean;
  [Key: string]: unknown;
};

export const handler: Handler = async (
  event: SsoUserEvent,
): Promise<SsoUserEventResponse> => {
  logJSON("Invoked with event", event);

  let userId: string;
  const data: { [Key: string]: unknown } = {};

  switch (event.RequestType) {
    case "Create":
      userId = await createUser(event);
      data.userId = { userId };
      break;
    case "Update":
      await updateUser(event);
      userId = event.PhysicalResourceId;
      break;
    case "Delete":
      await deleteUser(event);
      userId = event.PhysicalResourceId;
      break;
    default:
      throw new Error(`Unsupported request type.`);
  }
  const response: SsoUserEventResponse = {
    PhysicalResourceId: userId,
    Data: {
      UserId: userId, // Using Pascal case to match style of CloudFormation templates
    },
  };

  logJSON("Returning response", response);
  return response;
};

async function createUser(
  createUserEvent: SsoUserCreateEvent,
): Promise<string> {
  const props = eventPropsToAwsApiFormat(
    createUserEvent.ResourceProperties,
  ) as unknown as CreateUserCommandInput;
  logJSON("Creating user with props", props);
  const response = await identityStoreClient.send(new CreateUserCommand(props));
  if (!response.UserId)
    throw new Error("UserId was not returned from CreateUserCommand.");
  console.log(`Created user id" ${response.UserId}`);
  return response.UserId;
}

async function updateUser(event: SsoUserUpdateEvent): Promise<void> {
  const userId = event.PhysicalResourceId;
  const identityStoreId = event.ResourceProperties.identityStoreId;
  const newProps = eventPropsToAwsApiFormat(event.ResourceProperties);
  const oldProps = eventPropsToAwsApiFormat(event.OldResourceProperties);
  const changes = getUserUpdateOperations(oldProps, newProps);
  validateChanges(changes, oldProps);
  const commandProps: UpdateUserCommandInput = {
    UserId: userId,
    IdentityStoreId: identityStoreId,
    Operations: changes,
  };

  if (changes.length > 0) {
    logJSON("Updating user with props", commandProps);
    await identityStoreClient.send(new UpdateUserCommand(commandProps));
    console.log("Update successful.");
  } else {
    console.log("No changes to user attributes detected.");
  }
}

function validateChanges(
  changes: AttributeOperation[],
  originalProps: Record<string, unknown>,
) {
  for (const change of changes) {
    if (change.AttributePath === "userName") {
      throw new Error(
        `SSO usernames cannot be updated by CloudFormation. Please delete and recreate the user. In CDK, you can do this by changing the construct ID. Example: new SsoUser(this, "<newConstructId>", {userName: <newUsername>})`,
      );
    }
    if (change.AttributePath === "identityStore") {
      throw new Error(
        `Error: identityStore attribute cannot be changed for a user. Expected ${originalProps.IdentityStoreId} but received ${change.AttributeValue}`,
      );
    }
  }
}

async function deleteUser(
  event: CloudFormationCustomResourceDeleteEvent,
): Promise<void> {
  const props = {
    IdentityStoreId: event.ResourceProperties.identityStoreId,
    UserId: event.PhysicalResourceId,
  };
  if (event.ResourceProperties) logJSON("Deleting user with props", props);
  await identityStoreClient.send(new DeleteUserCommand(props));
  console.log("Deleting succeeded.");
}

function getUserUpdateOperations(
  oldAttr: Record<string, unknown>,
  newAttr: Record<string, unknown>,
): AttributeOperation[] {
  const operations: AttributeOperation[] = [];

  for (const key of Object.keys(newAttr)) {
    const oldValue = oldAttr[key];
    const newValue = newAttr[key];

    if (JSON.stringify(oldValue) !== JSON.stringify(newValue)) {
      console.log(`Change detected:${key}:\n`);
      logJSON(" - current", oldValue);
      logJSON(" - new", newValue);

      operations.push({
        AttributePath: firstCharacterToLowercase(key), // the createUser API expects PascalCase params, but updateUser expects camelCase
        AttributeValue: newValue as DocumentType,
      });
    }
  }
  return operations;
}

function firstCharacterToLowercase(input: string) {
  return input.charAt(0).toLowerCase() + input.slice(1);
}

/**
 * The identitystore createuser API expects user attributes in a format
 * that is verbose. In our CDK construct, we opted for a simpler structure
 * of construct properties for our SsoUser construct. This function
 * converts the simpler structure to the format that the identitystore
 * API expects.
 */
function eventPropsToAwsApiFormat(
  userEvent: CloudFormationSsoUserResourceProperties,
): Record<string, unknown> {
  const { userAttributes, identityStoreId } = userEvent;
  return {
    IdentityStoreId: identityStoreId,
    UserName: userAttributes.userName,
    Name: {
      FamilyName: userAttributes.lastName,
      GivenName: userAttributes.firstName,
      MiddleName: userAttributes.middleName,
    },
    DisplayName: `${userAttributes.firstName} ${userAttributes.lastName}`,
    Emails: userAttributes.email
      ? [
          {
            Value: userAttributes.email,
            Primary: true,
          },
        ]
      : undefined,
    PhoneNumbers: userAttributes.phoneNumber
      ? [
          {
            Value: userAttributes.phoneNumber,
            Primary: true,
          },
        ]
      : undefined,
    Title: userAttributes.title,
  };
}

function logJSON(message: string, data: unknown) {
  if (typeof data === "string") {
    console.log(`${message}: ${data}`);
  } else {
    console.log(`${message}: ${JSON.stringify(data, null, 2)}`);
  }
}
