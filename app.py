import aws_cdk as cdk
from sso import(
    SsoStack,
    SsoConfig
)

app = cdk.App()
SsoStack(
    app,
    "SsoStack",
    env=cdk.Environment(
        # If you have configured an additional account as a Delegated Administrator
        # of IAM Identity Center (SSO) in your AWS Organization, you can instead deploy
        # this stack to that account. Otherwise, you must deploy this in your org's
        # Management Account in the region where you've set up AWS IAM Identity Center.
        account=SsoConfig.sso_account.value,
        region=SsoConfig.sso_region.value
    ),
)

app.synth()