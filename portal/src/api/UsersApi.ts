import User, { UserLeaveAdministrator, UserRole } from "../models/User";
import BaseApi from "./BaseApi";
import routes from "../routes";

export default class UsersApi extends BaseApi {
  get basePath() {
    return routes.api.users;
  }

  get i18nPrefix() {
    return "users";
  }

  /**
   * Register a new user
   * @param requestData - Registration fields
   */
  createUser = async (requestData: Record<string, unknown>) => {
    const { data } = await this.request<User>(
      "POST",
      "",
      requestData,
      {},
      { excludeAuthHeader: true }
    );

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

  updateUser = async (user_id: string, patchData: Record<string, unknown>) => {
    const { data } = await this.request<User>("PATCH", user_id, patchData);
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
  convertUser = async (
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
