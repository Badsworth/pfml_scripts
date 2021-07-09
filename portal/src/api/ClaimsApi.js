import Claim, { AbsenceCaseStatus } from "../models/Claim";
import BaseApi from "./BaseApi";
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
   * @param {object} [filters]
   * @param {string} [filters.claim_status] - Comma-separated list of statuses
   * @param {string} [filters.employer_id]
   * @param {string} [filters.search]
   * @returns {Promise<{ claims: ClaimCollection, paginationMeta: PaginationMeta }>}
   */
  getClaims = async (pageOffset = 1, filters = {}) => {
    // We display Closed and Completed claims as the same to the user, so we
    // want the Closed filter to encompass both.
    const filterParams = { ...filters };
    if (
      filters &&
      filters.claim_status &&
      filters.claim_status.includes(AbsenceCaseStatus.closed)
    ) {
      filterParams.claim_status = `${filters.claim_status},${AbsenceCaseStatus.completed}`;
    }

    const { data, meta } = await this.request("GET", null, {
      page_offset: pageOffset,
      ...filterParams,
    });

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
      paginationMeta: meta ? new PaginationMeta(meta.paging) : null,
    };
  };
}
