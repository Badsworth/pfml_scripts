/* eslint-disable jsdoc/require-returns */
import { compact, map } from "lodash";
import BaseApi from "./BaseApi";
import User from "../models/User";
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
    const user_leave_administrators = this.transformUserLeaveAdministrators(
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
    const user_leave_administrators = this.transformUserLeaveAdministrators(
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

  // TODO (EMPLOYER-536): Remove helper method when API returns array of UserRole objects
  // [{ role: { role_description, role_id }}] --> [{ role_description, role_id }]
  transformUserRoles = (roles) => {
    return compact(map(roles, "role"));
  };

  // TODO (EMPLOYER-813): Remove helper method when API returns array of UserLeaveAdministrator objects
  // [{ employer: { employer_dba, employer_fein, employer_id }, verified}]
  // becomes
  // [{ employer_dba, employer_fein, employer_id, verified }]]
  transformUserLeaveAdministrators = (userLeaveAdministrators = []) => {
    return userLeaveAdministrators.map(({ employer, ...rest }) => {
      return {
        ...employer,
        ...rest,
      };
    });
  };
}
