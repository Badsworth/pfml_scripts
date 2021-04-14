/* eslint-disable jsdoc/require-returns */
import Claim, { ClaimEmployee, ClaimEmployer } from "../models/Claim";
import BaseApi from "./BaseApi";
import ClaimCollection from "../models/ClaimCollection";
import routes from "../routes";

export default class ClaimsApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
  }

  get i18nPrefix() {
    // TODO (CP-2077): Rename to "claims"
    return "apiClaims";
  }

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<{ claims: ClaimCollection }>}
   */
  getClaims = async () => {
    const { data } = await this.request("GET");

    const claims = data.map((claimData) => {
      claimData.employee = claimData.employee
        ? new ClaimEmployee(claimData.employee)
        : null;
      claimData.employer = claimData.employer
        ? new ClaimEmployer(claimData.employer)
        : null;

      return new Claim(claimData);
    });

    return {
      claims: new ClaimCollection(claims),
    };
  };
}
