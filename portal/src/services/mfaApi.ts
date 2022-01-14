import Auth, { CognitoUser } from "@aws-amplify/auth";
import { CognitoAuthError, CognitoError } from "../errors";
import tracker from "./tracker";

interface ErrorCodeMap {
  [code: string]: { field?: string; type: string } | undefined;
}

function isCognitoError(error: unknown): error is CognitoError {
  if (
    error &&
    typeof error === "object" &&
    error.hasOwnProperty("code") !== undefined
  ) {
    return true;
  }

  return false;
}

const errorCodeToIssueMap: ErrorCodeMap = {
  CodeDeliveryFailureException: { field: "code", type: "deliveryFailure" },
  InvalidParameterException: { type: "invalidParametersFallback" },
  UserNotFoundException: { type: "userNotFound" },
  LimitExceededException: { type: "attemptsLimitExceeded_updatePhone" },
};

const createCognitoError = (error: CognitoError) => {
  if (errorCodeToIssueMap[error.code]) {
    const issue = errorCodeToIssueMap[error.code];
    return new CognitoAuthError(error, issue);
  }
  return error;
};

export const verifyUserAttribute = async (
  user: CognitoUser,
  attribute: string
) => {
  try {
    tracker.trackFetchRequest("verifyUserAttribute");
    await Auth.verifyUserAttribute(user, attribute);
    tracker.markFetchRequestEnd();
  } catch (error) {
    if (isCognitoError(error)) {
      throw createCognitoError(error);
    }
    throw error;
  }
};
