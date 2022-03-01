import User, { UserLeaveAdministrator, UserRole } from "../models/User";
import BaseApi from "./BaseApi";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";

export default class UsersApi extends BaseApi {
  get basePath() {
    return routes.api.users;
  }

  /**
   * Figure out which feature flag headers to send to the back-end based on which feature flags
   * are enabled on the front-end.
   */
  get featureFlagHeaders() {
    const headers: { "X-FF-Sync-Cognito-Preferences"?: string } = {};

    // todo (PORTAL-1828): Remove claimantSyncCognitoPreferences feature flag
    if (isFeatureEnabled("claimantSyncCognitoPreferences")) {
      headers["X-FF-Sync-Cognito-Preferences"] = "true";
    }

    return headers;
  }

  get i18nPrefix() {
    return "users";
  }

  /**
   * Register a new user
   * @param requestData - Registration fields
   */
  createUser = async (requestData: { [key: string]: unknown }) => {
    const { data } = await this.request<User>("POST", "", requestData, {
      excludeAuthHeader: true,
    });

    return Promise.resolve({
      user: new User(data),
    });
  };

  /**
   * Get the currently authenticated user
   */
  getCurrentUser = async () => {
    const { data } = await this.request<User>("GET", "current");
    const roles = this.createUserRoles(data.roles);
    const user_leave_administrators = this.createUserLeaveAdministrators(
      data.user_leave_administrators
    );

    return Promise.resolve({
      user: new User({ ...data, roles, user_leave_administrators }),
    });
  };

  updateUser = async (
    user_id: string,
    patchData: { [key: string]: unknown }
  ) => {
    // todo (PORTAL-1828): Remove claimantSyncCognitoPreferences feature flag
    const { data } = await this.request<User>("PATCH", user_id, patchData, {
      additionalHeaders: this.featureFlagHeaders,
    });
    const roles = this.createUserRoles(data.roles);
    const user_leave_administrators = this.createUserLeaveAdministrators(
      data.user_leave_administrators
    );

    return {
      user: new User({
        ...patchData,
        ...data,
        roles,
        user_leave_administrators,
      }),
    };
  };

  /**
   * Convert a user to an employer
   */
  convertUserToEmployer = async (
    user_id: string,
    postData: { employer_fein: string }
  ) => {
    const { data } = await this.request<User>(
      "POST",
      `${user_id}/convert_employer`,
      postData
    );
    const roles = this.createUserRoles(data.roles);
    const user_leave_administrators = this.createUserLeaveAdministrators(
      data.user_leave_administrators
    );

    return {
      user: new User({
        ...data,
        roles,
        user_leave_administrators,
      }),
    };
  };

  createUserLeaveAdministrators = (
    leaveAdmins: UserLeaveAdministrator[] = []
  ) => {
    return leaveAdmins.map(
      (leaveAdmin) => new UserLeaveAdministrator(leaveAdmin)
    );
  };

  createUserRoles = (roles: UserRole[] = []) => {
    return roles.map((role) => new UserRole(role));
  };
}
