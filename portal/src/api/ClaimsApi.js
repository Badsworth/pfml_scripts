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
    return "claims";
  }

  /**
   * Fetches a page of claims for a user
   * @param {number|string} pageOffset - Page number to load
   * @param {{ employer_id: string }} [filters]
   * @returns {Promise<{ claims: ClaimCollection, paginationMeta: PaginationMeta }>}
   */
  getClaims = async (pageOffset = 1, filters = {}) => {
    const { data, meta } = await this.request("GET", null, {
      page_offset: pageOffset,
      ...filters,
    });

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
      paginationMeta: meta ? new PaginationMeta(meta.paging) : null,
    };
  };
}
