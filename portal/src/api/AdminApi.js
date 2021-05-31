import User, { RoleDescription } from "../models/User";
import BaseApi from "./BaseApi";

export default class AdminApi extends BaseApi {
  get basePath() {
    return "/admin";
  }

  get i18nPrefix() {
    return "admin";
  }

  /**
   * Fetches the current
   *
   * @returns {Promise<{ maintenanceStatus: maintenanceStatus }>}
   */
  getUsers = async () => {
    const { data } = await this.request("GET", "users");
    return data.map((user) => new User(user));
  };

  /**
   * Sends self-service email to specific user with instrutions
   * on how to convert their account to a different role
   * @param {string} user_id
   * @param {RoleDescription} role
   * @returns {Promise<{ emailSent: boolean }>}
   */
  convertUserToRole = async (user_id, role) => {
    const { data } = await this.request(
      "POST",
      `users/${user_id}/convert_${role.toLowerCase()}`,
      {}
    );
    return data;
  };

  convertUserToEmployer = async (user_id) => {
    return await this.convertUserToRole(user_id, RoleDescription.employer);
  };

  convertUserToClaimant = async (user_id) => {
    return await this.convertUserToRole(user_id, RoleDescription.claimant);
  };
}
