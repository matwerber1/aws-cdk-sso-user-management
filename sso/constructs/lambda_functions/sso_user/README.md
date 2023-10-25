# Lambda function for SSO User Custom Resources

This directory contains the source code for a Python Lambda function that acts as a [CloudFormation Custom Resource handler](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html) to allow us to create, update, and delete AWS SSO users in our AWS Organization.

## What this function does

We created this function because, at the time of this writing, SSO users are not supported by CloudFormation natively. This function uses the `identitystore` module of the AWS SDK in Python to create, update, and delete AWS SSO users.

This function uses the [AWS CDK Provider Framework](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html), which is a wrapper around the native AWS CloudFormation custom resource type and greatly simplifies the process of creating custom resources.

## How it gets deployed

As you'll see in our SsoUser CDK construct ([../../sso_user.py](../../sso_user.py)), CDK makes Lambda function deployment easy:

```python
lambda_.Function(
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="index.on_event",
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
    environment={
        "SSO_IDENTITY_STORE_ID": sso_identity_store_id,
        "SSO_INSTANCE_ARN": sso_instance_arn,
        "SSO_REGION": sso_region,
    },
)
```

The line `aws_cdk.lambda.Code.from_asset(..)` is all we need to tell CDK to zip the contents of a directory and upload it to a secure S3 bucket in our account, and use it as a Lambda `Zip archive` for deployment. We can install additional dependencies locally in the folder, though we opt for the even easier approach of simply including a `requirements.txt` in `BundlingOptions`, which tells CDK to create a local Docker image, run pip install, push the image to ECR, and create a Docker-backed Lambda function from that image.
