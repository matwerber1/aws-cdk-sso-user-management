import json
import os
from pprint import pprint
from typing import List, Optional, TypedDict, Union, Mapping, Sequence, Any, cast

import boto3
from deepdiff.diff import DeepDiff
from typing_extensions import NotRequired, Required

ALLOW_CREATE_REQUEST_TO_IMPORT_EXISTING_USER = True
ALLOW_DELETE_USERS = False
RETURN_DELETE_SUCCESS_EVEN_IF_DELETE_NOT_ALLOWED = (
    True  # i.e. retain users if removed from a stack
)

NameTypeDef = TypedDict(
    "NameTypeDef",
    {
        "Formatted": NotRequired[str],
        "FamilyName": NotRequired[str],
        "GivenName": NotRequired[str],
        "MiddleName": NotRequired[str],
        "HonorificPrefix": NotRequired[str],
        "HonorificSuffix": NotRequired[str],
    },
)

EmailTypeDef = TypedDict(
    "EmailTypeDef",
    {
        "Value": NotRequired[str],
        "Type": NotRequired[str],
        "Primary": NotRequired[bool],
    },
)

AttributeOperationTypeDef = TypedDict(
    "AttributeOperationTypeDef",
    {
        "AttributePath": str,
        "AttributeValue": NotRequired[Mapping[str, Any]],
    },
)

class SsoUserAttributesFromCloudFormationEvent(TypedDict):
    username: Required[str]
    first_name: Required[str]
    last_name: Required[str]
    email: Required[str]
    title: NotRequired[str]


class SsoUserBaseEventFromCloudFormation(TypedDict):
    """
    This is the event passed to the Lambda function. Since we are using CDK's Provider Framework,
    this event is slightly different from the native event that would be passed CloudFormation.
    See: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html
    """

    RequestType: Required[str]
    LogicalResourceId: Required[str]
    ResourceType: Required[str]
    RequestId: Required[str]
    StackId: Required[str]
    ResourceProperties: Required[SsoUserAttributesFromCloudFormationEvent]


class SsoUserCreateEvent(SsoUserBaseEventFromCloudFormation):
    pass


class SsoUserUpdateEvent(SsoUserBaseEventFromCloudFormation):
    PhysicalResourceId: Required[str]
    OldResourceProperties: Required[SsoUserAttributesFromCloudFormationEvent]


class SsoUserDeleteEvent(SsoUserBaseEventFromCloudFormation):
    PhysicalResourceId: Required[str]


class IdentityStoreUserAttributesName(TypedDict):
    FamilyName: str
    GivenName: str


class IdentityStoreUserAttributesEmail(TypedDict):
    Value: str
    Type: str
    Primary: bool


class IdentityStoreUserAttributes(TypedDict):
    """
    Matches API specification for identitystore.create_user(), though only for attributes
    we've chosen to support. You can add more if needed by building out this and related
    code further. Note: intentionally excluding IdentityStoreId, since we don't want the
    CDK user to have to provide this value with each new user as it won't change. Instead,
    the Lambda function pulls the identity store id from environment variables.
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/identitystore/client/create_user.html
    """

    UserName: str
    Name: NameTypeDef
    DisplayName: str
    Emails: Sequence[EmailTypeDef]


class IdentityStoreUser(IdentityStoreUserAttributes):
    IdentityStoreId: str
    UserId: str


class ChangeOperation(TypedDict):
    """
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/identitystore/client/update_user.html

    Note: Even though docs claim AttributePath supports JMESPath, as best I can tell
    it only supports top-level keys in the IdentityStoreUserAttributes rather than
    being able to use dot notation for more deeply-nested keys.
    """

    AttributePath: str
    AttributeValue: Union[str, int, float, bool, List, dict, None]


class CdkCustomResourceResponse(TypedDict):
    """
    Any successful operation should return a response like below, and
    errors should be raised as exceptions. Since we're using CDK's
    Provider Framework, note that this is a slightly different from
    how responses are handled with a native CloudFormation Custom Resource.
    """

    PhysicalResourceId: Required[str]
    Data: NotRequired[dict]
    NoEcho: NotRequired[bool]


SSO_IDENTITY_STORE_ID = os.environ.get("SSO_IDENTITY_STORE_ID") or ""
SSO_REGION = os.environ.get("SSO_REGION") or ""

if not SSO_IDENTITY_STORE_ID or not SSO_REGION:
    raise Exception(
        "SSO_IDENTITY_STORE_ID and SSO_REGION environment variables must be set"
    )

identitystore_client = boto3.client("identitystore", region_name=SSO_REGION)


def on_event(event: SsoUserBaseEventFromCloudFormation, context):
    print(f"Received event:\n{json.dumps(event, indent=2)}")
    request_type = event["RequestType"]
    print(f"Request type: {request_type}")
    if request_type == "Create":
        return on_create(cast(SsoUserCreateEvent, event))
    if request_type == "Update":
        return on_update(cast(SsoUserUpdateEvent, event))
    if request_type == "Delete":
        return on_delete(cast(SsoUserDeleteEvent, event))
    raise Exception("Invalid request type: %s" % request_type)


def firstCharacterToLower(s: str) -> str:
    return s[0].lower() + s[1:]

def toAwsIdentityStoreUserFormat(
    cdk_user_attr: SsoUserAttributesFromCloudFormationEvent,
) -> IdentityStoreUserAttributes:
    """
    The identitystore APIs expect user attributes to be provided in a verbose. We use
    a simpler format when collecting the attributes from you in CDK and passing them
    to Lambda, then convert to API-ready format with this function.
    """
    identitystore_user_attr = IdentityStoreUserAttributes(
        UserName=cdk_user_attr["username"],
        Name={
            "GivenName": cdk_user_attr["first_name"],
            "FamilyName": cdk_user_attr["last_name"],
        },
        DisplayName=cdk_user_attr["first_name"] + " " + cdk_user_attr["last_name"],
        Emails=[
            {
                "Value":cdk_user_attr["email"],
                "Type":"work",  # To stay consistent with how AWS web console creates users, do not change
                "Primary":True,
            }
        ],
    )
    return identitystore_user_attr


def on_create(event: SsoUserCreateEvent) -> CdkCustomResourceResponse:
    new_user_attributes = toAwsIdentityStoreUserFormat(event["ResourceProperties"])
    existing_user = get_existing_user_if_exists(new_user_attributes["UserName"])
    if existing_user:
        return try_import_existing_user(existing_user, new_user_attributes)
    print(f"Creating user with attributes: {json.dumps(new_user_attributes, indent=2)}")
    response = identitystore_client.create_user(
        IdentityStoreId=SSO_IDENTITY_STORE_ID, **new_user_attributes
    )
    physical_id = response["UserId"]
    print(f'Created user {response["UserId"]}')
    return CdkCustomResourceResponse(
        PhysicalResourceId=physical_id,
        Data={
            "UserId": physical_id,
            "Arn": f"arn:{SSO_REGION}:identitystore:::user/{physical_id}",
            "IdentityStoreId": SSO_IDENTITY_STORE_ID,
        },
    )


def on_update(event: SsoUserUpdateEvent) -> CdkCustomResourceResponse:
    physical_id = event["PhysicalResourceId"]
    new_user_attr = toAwsIdentityStoreUserFormat(event["ResourceProperties"])
    old_user_attr = toAwsIdentityStoreUserFormat(event["OldResourceProperties"])
    change_operations: List[AttributeOperationTypeDef] = []
    ddiff = DeepDiff(old_user_attr, new_user_attr)
    print("Differences between new and old attributes:")
    pprint(ddiff, indent=2)
    for changed_key in ddiff.affected_root_keys:
        key = cast(str, changed_key)
        newValue = cast(Mapping[str, Any], new_user_attr.get(key))
        change_operations.append({
                # identitystore.update_user() expects lower camel case whereas
                # identitystore.create_user() expects upper camel case
                "AttributePath":firstCharacterToLower(key),
                "AttributeValue": newValue,
        }
        )
    print("Change operations for identitystore.update_user() API:")
    pprint(change_operations, indent=2)
    identitystore_client.update_user(
        IdentityStoreId=SSO_IDENTITY_STORE_ID,
        UserId=physical_id,
        Operations=change_operations,
    )
    print("Update completed.")
    return CdkCustomResourceResponse(
        PhysicalResourceId=physical_id,
    )


def on_delete(event: SsoUserDeleteEvent) -> CdkCustomResourceResponse:
    # One of several ways to approach this...
    physical_id = event["PhysicalResourceId"]
    print("Deleting user {physical_id}")
    if not ALLOW_DELETE_USERS:
        if not RETURN_DELETE_SUCCESS_EVEN_IF_DELETE_NOT_ALLOWED:
            raise Exception(
                "Deleting users not allowed. Either set ALLOW_DELETE_USERS = True, or to remove a user from a stack but not delete them, set RETURN_DELETE_SUCCESS_EVEN_IF_DELETE_NOT_ALLOWED = True"
            )
    else:
        identitystore_client.delete_user(
            IdentityStoreId=SSO_IDENTITY_STORE_ID, UserId=physical_id
        )

    return CdkCustomResourceResponse(
        PhysicalResourceId=physical_id,
    )


def get_existing_user_if_exists(username):
    """If user doesn't exist, return False"""
    print("Checking if {username} already exists...")
    response = identitystore_client.list_users(
        IdentityStoreId=SSO_IDENTITY_STORE_ID,
        Filters=[{"AttributePath": "UserName", "AttributeValue": username}],
    )
    user_exists = len(response.get("Users", [])) > 0
    if user_exists:
        existing_user = cast(IdentityStoreUser, response["Users"][0])
        print(
            f"Found existing user ID {existing_user['UserId']} for username {username}"
        )
        return existing_user
    else:
        print(f"Username {username} does not exist")
        return False


def try_import_existing_user(
    existing_user: IdentityStoreUser, new_user_attributes: IdentityStoreUserAttributes
):
    """
    If an SSO user was created outside of this CDK project and we want to manage it with this
    project going forward, this function will check whether the CDK-defined user is identical to
    the "new" user being requested for all attributes except (of course) the unique user ID.
    If the existing user matches all other user attributes requested, we will simply return the existing
    user ID as the PhysicalResourceId response to make CloudFormation think the create was successful.
    This should only be used when a user was created by mistake (or before we moved to CDK) on an
    exception basis.
    Use ALLOW_CREATE_REQUEST_TO_IMPORT_EXISTING_USER=True to allow this feature.
    """
    # downcast so we can perform a fair comparison
    existing_user_id = existing_user["UserId"]
    username = new_user_attributes["UserName"]
    existing_user_attributes = cast(
        IdentityStoreUserAttributes,
        {
            key: value
            for key, value in existing_user.items()
            if key not in ["IdentityStoreId", "UserId"]
        },
    )
    if not ALLOW_CREATE_REQUEST_TO_IMPORT_EXISTING_USER:
        raise Exception(
            f"Conflict: Requested UserName {username} taken by existing user ID "
            "{existing_user_id}. If user created outside of CDK and you want to "
            "bring them in to CDK management, set ALLOW_CREATE_REQUEST_TO_IMPORT_EXISTING_USER=True"
            "in Lambda resource handler"
        )
    diff = DeepDiff(
        new_user_attributes,
        existing_user_attributes,
        ignore_order=True,
    )
    pprint(diff, indent=2)
    if diff:
        raise Exception(
            f"Username {username} already taken by pre-existing user ID {existing_user_id}. "
            "Attempt to import skipped because user properties in template do not match "
            "pre-existing user properties"
        )
    else:
        print(
            "New user requested, but username already taken. Returning existing user ID "
            f"{existing_user_id} as PhysicalResourceId to CloudFormation to 'import' the "
            "user to your stack"
        )
        return CdkCustomResourceResponse(
            PhysicalResourceId=existing_user_id,
            Data={
                "UserId": existing_user_id,
                "Arn": f"arn:{SSO_REGION}:identitystore:::user/{existing_user_id}",
                "IdentityStoreId": SSO_IDENTITY_STORE_ID,
            },
        )