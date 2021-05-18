import BaseApi from "./BaseApi";
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import PaginationMeta from "../models/PaginationMeta";
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
   * Fetches a page of claims for a user
   * @param {number} pageOffset - page number to load
   * @returns {Promise<{ claims: ClaimCollection, paginationMeta: PaginationMeta }>}
   */
  getClaims = async (pageOffset = 1) => {
    const { data, meta } = await this.request("GET", null, {
      page_offset: pageOffset,
    });

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
      paginationMeta: meta ? new PaginationMeta(meta.paging) : null,
    };
  };
}
