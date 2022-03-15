import BaseApi from "./BaseApi";
import { RoleDescription } from "../models/User";
import routes from "../routes";

export default class RolesApi extends BaseApi {
  get basePath() {
    return routes.api.roles;
  }

  get namespace() {
    return "roles";
  }

  /**
   * Convert a user to a Employee
   */
  deleteEmployerRole = async (user_id: string) => {
    await this.request<never>("DELETE", "", {
      role: {
        role_description: RoleDescription.employer,
      },
      user_id,
    });
  };
}
