/* eslint-disable jsdoc/require-returns */
import { compact, map } from "lodash";
import BaseApi from "./BaseApi";
import User from "../models/User";
import routes from "../routes";

/**
 * @typedef {{ success: boolean, user: User }} UsersApiResult
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
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
    const { data, status } = await this.request("GET", "current", null);
    const roles = this.transformUserRoles(data.roles);

    return Promise.resolve({
      success: true,
      status,
      user: new User({ ...data, roles }),
    });
  };

  /**
   * Update a user
   * @param {object} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @returns {Promise<UsersApiResult>}
   */
  updateUser = async (user_id, patchData) => {
    const { data, status } = await this.request("PATCH", user_id, patchData);
    const roles = this.transformUserRoles(data.roles);

    return {
      success: true,
      status,
      user: new User({
        ...patchData,
        ...data,
        roles,
      }),
    };
  };

  // TODO (EMPLOYER-536): Remove helper method when API returns array of UserRole objects
  // [{ role: { role_description, role_id }}] --> [{ role_description, role_id }]
  transformUserRoles = (roles) => {
    return compact(map(roles, "role"));
  };
}
