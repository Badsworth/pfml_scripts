import { Issue } from "../errors";

function validateCode(code?: string): Issue | undefined {
  if (!code) {
    return {
      field: "code",
      type: "required",
      namespace: "mfa",
    };
  } else if (!code.match(/^\d{6}$/)) {
    return {
      field: "code",
      type: "pattern", // matches same type as API regex pattern validations
      namespace: "mfa",
    };
  }
}

export default validateCode;
