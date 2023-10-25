from enum import Enum

class AwsAccounts(str, Enum):
    """List of your AWS accounts with friendly names.
    You can use whatever name you want for other accounts, and you do not need 
    to actually list accounts unless you want to use them with this solution.
    """
    MANAGEMENT: str = "999999999999"
    LOG_ARCHIVE: str = "111111111111"
    AUDIT: str = "222222222222"
    SANDBOX: str = "333333333333"

class SsoConfig(str, Enum):
    """Your AWS Organization-specific SSO configuration as set up in your org management account.
    """
    sso_account = "999999999999"
    sso_region = "us-east-1"
    identity_store_id = "d-xxxxxxxxxx"
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"