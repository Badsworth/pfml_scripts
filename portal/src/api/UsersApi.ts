/* eslint-disable jsdoc/require-returns */
import User, { UserLeaveAdministrator, UserRole } from "../models/User";

import BaseApi from "./BaseApi";
import routes from "../routes";

/**
 * @typedef {{ user: User }} UsersApiResult
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

export default class UsersApi extends BaseApi {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'basePath' in type 'UsersApi' is not assi... Remove this comment to see the full error message
  get basePath() {
    return routes.api.users;
  }

  // @ts-expect-error ts-migrate(2416) FIXME: Property 'i18nPrefix' in type 'UsersApi' is not as... Remove this comment to see the full error message
  get i18nPrefix() {
    return "users";
  }

  /**
   * Register a new user
   * @param {object} requestData - Registration fields
   * @returns {Promise<UsersApiResult>}
   */
  createUser = async (requestData) => {
    const { data } = await this.request(
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
   * @returns {Promise<UsersApiResult>}
   */
  getCurrentUser = async () => {
    const { data } = await this.request("GET", "current", null);
    const roles = this.createUserRoles(data.roles);
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
   * Convert a user role to another
   * @param {string} user_id - ID of user being converted
   * @param {object} postData - User fields to update - role and leave admin
   * @returns {Promise<UsersApiResult>}
   */
  convertUser = async (user_id, postData) => {
    const { data } = await this.request(
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

  createUserLeaveAdministrators = (leaveAdmins) => {
    return (leaveAdmins || []).map(
      (leaveAdmin) => new UserLeaveAdministrator(leaveAdmin)
    );
  };

  createUserRoles = (roles) => {
    return (roles || []).map((role) => new UserRole(role));
  };
}
