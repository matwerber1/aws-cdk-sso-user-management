import os
from typing import TypedDict, cast

from aws_cdk import BundlingOptions, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import custom_resources as cr
from cdk_nag import NagPackSuppression as Nag
from cdk_nag import NagSuppressions
from cdk_nag import RegexAppliesTo as NagRegex
from constructs import Construct

from .. import SsoConfig

dirname = os.path.dirname(__file__)


class SsoUserAttributes(TypedDict):
    username: str
    first_name: str
    last_name: str
    email: str


class SsoUserProvider(Construct):
    """
    Docs at: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.custom_resources/README.html
    """

    service_token: str
    provider: cr.Provider

    @classmethod
    def get_or_create(cls, scope: Construct) -> cr.Provider:
        stack = Stack.of(scope)
        id = "Custom::SsoUser"
        provider= cast(cr.Provider, stack.node.try_find_child(id))
        if provider is None:
            provider = SsoUserProvider(stack, id)
        return provider

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        stack = Stack.of(scope)
        region = stack.region
        account = stack.account
        provider_framework_function_name = (
            f"{stack.stack_name}-CustomSsoUser-CdkProvider"
        )
        on_event_handler_function_name = (
            f"{stack.stack_name}-CustomSsoUser-onEventHandler"
        )

        on_event_handler_role = iam.Role(
            self,
            id="OnEventFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "CloudWatchLogPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            resources=[f"arn:aws:logs:{region}:{account}:*"],
                            actions=["logs:CreateLogGroup"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                            resources=[
                                f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{on_event_handler_function_name}*"
                            ],
                        ),
                    ]
                ),
                "SsoUserPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "identitystore:CreateUser",
                                "identitystore:DeleteUser",
                                "identitystore:UpdateUser",
                                "identitystore:ListUsers",
                            ],
                            resources=[
                                f"arn:aws:identitystore::{account}:identitystore/{SsoConfig.identity_store_id.value}",  # ARN used to create,
                                "arn:aws:identitystore:::user/*",  # ARN used to update and delete
                            ],
                        )
                    ]
                ),
            },
        )

        on_event_handler_function = lambda_.Function(
            self,
            id="OnEventFunction",
            function_name=on_event_handler_function_name,
            runtime=lambda_.Runtime.PYTHON_3_11,
            role=on_event_handler_role,
            code=lambda_.Code.from_asset(
                os.path.join(dirname, "lambda_functions/sso_user"),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            handler="index.on_event",
            environment={
                "SSO_IDENTITY_STORE_ID": SsoConfig.identity_store_id.value,
                "SSO_INSTANCE_ARN": SsoConfig.instance_arn.value,
                "SSO_REGION": SsoConfig.sso_region.value,
            },
        )

        self.provider = cr.Provider(
            stack,
            id="Provider",
            on_event_handler=on_event_handler_function,
            provider_function_name=provider_framework_function_name,
        )

        self.service_token = self.provider.service_token

        NagSuppressions.add_resource_suppressions(
            construct=on_event_handler_role,
            apply_to_children=True,
            suppressions=[
                Nag(
                    id="AwsSolutions-IAM5",
                    reason="minimum ability for Lambda to write logs to CloudWatch",
                    applies_to=[
                        f"Resource::arn:aws:logs:{region}:{account}:*",
                        f"Resource::arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{on_event_handler_function_name}*",
                        NagRegex(
                            regex="\/Resource::<CustomSsoUserOnEventFunction.{8}\.Arn>:\*/"
                        ),
                    ],
                ),
                Nag(
                    id="AwsSolutions-IAM5",
                    reason="Allow our Lambda to create, modify, or delete SSO users",
                    applies_to=[
                        "Resource::arn:aws:identitystore:::user/*",
                    ],
                ),
            ],
        )

        NagSuppressions.add_resource_suppressions_by_path(
            stack=stack,
            path="/SsoStack/Provider/framework-onEvent",
            apply_to_children=True,
            suppressions=[
                Nag(
                    id="AwsSolutions-IAM4",
                    reason="Safe - only allows CDK-created helper function to write logs to CloudWatch",
                    applies_to=[
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                ),
                Nag(
                    id="AwsSolutions-IAM5",
                    reason="Safe - allows helper function to invoke our OnEvent function to proxy request/response to/from CloudFormation",
                    applies_to=[
                        NagRegex(
                            regex="\/Resource::<CustomSsoUserOnEventFunction.{8}\.Arn>:\*/"
                        ),
                    ],
                ),
            ],
        )