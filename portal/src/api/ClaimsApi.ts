import Claim, { AbsenceCaseStatus } from "../models/Claim";
import ApiResourceCollection from "../models/ApiResourceCollection";
import BaseApi from "./BaseApi";
import ClaimDetail from "../models/ClaimDetail";
import routes from "../routes";

export interface GetClaimsParams {
  page_offset?: string | number;
  employer_id?: string;
  search?: string;
  // TODO (PORTAL-1560): Remove claim_status
  claim_status?: string;
  allow_hrd?: boolean;
  is_reviewable?: "no" | "yes";
  order_by?: // TODO (PORTAL-1560): Remove absence_status and fineos_absence_status
  | "absence_status"
    | "fineos_absence_status"
    | "created_at"
    | "employee"
    | "latest_follow_up_date";
  order_direction?: "ascending" | "descending";
  request_decision?:
    | "approved"
    | "cancelled"
    | "denied"
    | "pending"
    | "withdrawn";
}

export default class ClaimsApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
  }

  get namespace() {
    return "claims";
  }

  /**
   * Fetches a page of claims for a user
   * @param filters.claim_status - Comma-separated list of statuses
   */
  getClaims = async (params: GetClaimsParams = {}) => {
    const activeParams = { ...params };

    // We display Closed and Completed claims as the same to the user, so we
    // want the Closed filter to encompass both.
    if (
      params.claim_status &&
      params.claim_status.includes(AbsenceCaseStatus.closed)
    ) {
      activeParams.claim_status = `${params.claim_status},${AbsenceCaseStatus.completed}`;
    }

    // We want to avoid exposing "Fineos" terminology in user-facing interactions,
    // so we support just "absence_status" everywhere we set order_by (like the user's
    // URL query string).
    if (params.order_by === "absence_status") {
      activeParams.order_by = "fineos_absence_status";
    }
    if (params.page_offset === undefined) {
      activeParams.page_offset = 1;
    }

    const { data, meta } = await this.request<Claim[]>("GET", "", {
      ...activeParams,
    });

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ApiResourceCollection<Claim>("fineos_absence_id", claims),
      paginationMeta: meta?.paging ?? {},
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
