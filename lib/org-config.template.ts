const orgConfig = {
  sso: {
    identityStoreId: "d-XXXXXXXXXX",
    requireUsernameAsEmail: true,
    allowedEmailDomains: ["example.com"],
    instanceArn: "arn:aws:sso:::instance/ssoins-XXXXXXXXXXXXXXXX",
    region: "<YOUR_SSO_REGION>",
  },
  accounts: {
    management: "999999999999",
    audit: "999999999999",
    logArchive: "999999999999",
    backup: "999999999999",
    sandbox: "999999999999",
    production: "999999999999",
    staging: "999999999999",
  },
};

export type OrgConfig = (typeof orgConfig)[keyof typeof orgConfig];
export { orgConfig };
