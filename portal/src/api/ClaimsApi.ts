import ApiResourceCollection from "../models/ApiResourceCollection";
import BaseApi from "./BaseApi";
import Claim from "../models/Claim";
import ClaimDetail from "../models/ClaimDetail";
import routes from "../routes";

export interface GetClaimsParams {
  page_offset?: string | number;
  employer_id?: string;
  search?: string;
  allow_hrd?: boolean;
  is_reviewable?: "no" | "yes";
  order_by?: "created_at" | "employee" | "latest_follow_up_date";
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
   */
  getClaims = async (params: GetClaimsParams = {}) => {
    const activeParams = { ...params };

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
