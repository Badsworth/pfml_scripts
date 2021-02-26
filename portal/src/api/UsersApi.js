/* eslint-disable jsdoc/require-returns */
import User, { UserLeaveAdministrator, UserRole } from "../models/User";
import BaseApi from "./BaseApi";
import routes from "../routes";

/**
 * @typedef {{ user: User }} UsersApiResult
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

export default class UsersApi extends BaseApi {
  get basePath() {
    return routes.api.users;
  }

  get i18nPrefix() {
    return "users";
  }

  /**
   * Get the currently authenticated user
   * @returns {Promise<UsersApiResult>}
   */
  getCurrentUser = async () => {
    const { data } = await this.request("GET", "current", null);
    const roles = this.transformUserRoles(data.roles);
    const user_leave_administrators = this.createUserLeaveAdministrators(
      data.user_leave_administrators
    );

    return Promise.resolve({
      user: new User({ ...data, roles, user_leave_administrators }),
    });
  };

  /**
   * Update a user
   * @param {object} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @returns {Promise<UsersApiResult>}
   */
  updateUser = async (user_id, patchData) => {
    const { data } = await this.request("PATCH", user_id, patchData);
    const roles = this.transformUserRoles(data.roles);
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

  createUserLeaveAdministrators = (leaveAdmins) => {
    return (leaveAdmins || []).map(
      (leaveAdmin) => new UserLeaveAdministrator(leaveAdmin)
    );
  };

  // TODO (EMPLOYER-963): Remove helper method when API returns array of UserRole objects
  // Accepts [{ role: { role_description, role_id }}] or [{ role_description, role_id }]
  // Returns [{ role_description, role_id }]
  transformUserRoles = (roles) => {
    return roles.map((r) => {
      const role = r.role || r;
      return new UserRole(role);
    });
  };
}
