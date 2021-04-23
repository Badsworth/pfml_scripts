import BaseApi from "./BaseApi";
import Claim from "../models/Claim";
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
   *
   * @param {number} page - zero-based page index
   * @returns {Promise<{ claims: ClaimCollection }>}
   */
  getClaims = async (page) => {
    const { data } = await this.request("GET", `?page=${page}`);

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
    };
  };
}
