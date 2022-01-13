import Claim, { AbsenceCaseStatus } from "../models/Claim";
import ClaimDetail, { Payments } from "../models/ClaimDetail";
import BaseApi from "./BaseApi";
import ClaimCollection from "../models/ClaimCollection";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";

export default class ClaimsApi extends BaseApi {
  // payments and claims calls use different base paths
  get basePath() {
    return "";
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
      allow_hrd?: boolean;
    } = {}
  ) => {
    const orderParams = { ...order };
    // We display Closed and Completed claims as the same to the user, so we
    // want the Closed filter to encompass both.
    // TODO (PFMLPB-2615) Remove this feature flag after HRD feature is enabled
    const employerUnlockDashboard: boolean = isFeatureEnabled(
      "employerUnlockDashboard"
    );
    // Depending on whether the employerUnlockDashboard feature flag is enabled or not,
    // We ask the API to allow/block this HRD LA from seeing claims in the dashboard
    if (employerUnlockDashboard) {
      filters.allow_hrd = employerUnlockDashboard;
    }
    const filterParams = { ...filters };

    if (
      filters.claim_status &&
      filters.claim_status.includes(AbsenceCaseStatus.closed)
    ) {
      filterParams.claim_status = `${filters.claim_status},${AbsenceCaseStatus.completed}`;
    }

    // We want to avoid exposing "Fineos" terminology in user-facing interactions,
    // so we support just "absence_status" everywhere we set order_by (like the user's
    // URL query string).
    if (order.order_by && order.order_by === "absence_status") {
      orderParams.order_by = "fineos_absence_status";
    }

    const { data, meta } = await this.request<Claim[]>(
      "GET",
      routes.api.claims,
      {
        page_offset: pageOffset,
        ...orderParams,
        ...filterParams,
      }
    );

    const claims = data.map((claimData) => new Claim(claimData));

    return {
      claims: new ClaimCollection(claims),
      paginationMeta: meta?.paging ?? {},
    };
  };

  /**
   * Fetches claim details given a FINEOS absence ID
   */
  getClaimDetail = async (absenceId: string) => {
    const { data } = await this.request<ClaimDetail>(
      "GET",
      `${routes.api.claims}/${absenceId}`
    );
    return {
      claimDetail: new ClaimDetail(data),
    };
  };

  getPayments = async (absenceId: string) => {
    const { data } = await this.request<Payments>(
      "GET",
      `${routes.api.payments}?absence_case_id=${absenceId}`
    );
    return data;
  };
}
