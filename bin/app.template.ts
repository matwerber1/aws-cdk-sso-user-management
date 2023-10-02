#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { SsoConfigurationStack } from "../lib/org-sso-stack";

const app = new cdk.App();
new SsoConfigurationStack(app, "SsoStack", {
  env: {
    account: "<YOUR MANAGEMENT ACCOUNT ID>",
    region: "<YOUR REGION WHERE AWS SSO / IDENTITY CENTER CREATED>",
  },
  stackName: "cdk-organization-sso",
});
