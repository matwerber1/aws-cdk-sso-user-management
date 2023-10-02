import { SsoUser } from "./SsoUser";
import {
  SsoGroupAssignment,
  SsoGroupAssignmentConstructor,
} from "./SsoGroupAssignment";
import { SsoConfigProps } from "./types";

export function config(configuration: SsoConfigProps) {
  SsoUser.config(configuration);
  SsoGroupAssignment.config(configuration);
}

export { SsoUser, SsoGroupAssignment, SsoGroupAssignmentConstructor };
