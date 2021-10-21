import Claim, { AbsenceCaseStatus } from "../models/Claim";
import BaseApi from "./BaseApi";
import ClaimCollection from "../models/ClaimCollection";
import ClaimDetail from "../models/ClaimDetail";
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
   * @param filters.claim_status - Comma-separated list of statuses
   */
  getClaims = async (
    pageOffset: string | number = 1,
    order: {
      order_by?: string;
      order_direction?: "ascending" | "descending";
    } = {},
    filters: {
      claim_status?: string;
      employer_id?: string;
      search?: string;
    } = {}
  ) => {
    const orderParams = { ...order };
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

    // We want to avoid exposing "Fineos" terminology in user-facing interactions,
    // so we support just "absence_status" everywhere we set order_by (like the user's
    // URL query string).
    if (order && order.order_by && order.order_by === "absence_status") {
      orderParams.order_by = "fineos_absence_status";
    }

    const { data, meta } = await this.request<Claim[]>("GET", undefined, {
      page_offset: pageOffset,
      ...orderParams,
      ...filterParams,
    });

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
      paginationMeta: new PaginationMeta(meta ? meta.paging : {}),
    };
  };

  /**
   * Fetches claim details given a FINEOS absence ID
   */
  getClaimDetail = async (absenceId: string) => {
    const { data } = await this.request<ClaimDetail>("GET", absenceId);

    return {
      claimDetail: new ClaimDetail(data),
    };
  };
}
