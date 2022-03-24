import ApiResourceCollection from "../models/ApiResourceCollection";
import BaseApi from "./BaseApi";
import BenefitsApplication from "../models/BenefitsApplication";
import PaymentPreference from "../models/PaymentPreference";
import TaxWithholdingPreference from "../models/TaxWithholdingPreference";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";

export default class BenefitsApplicationsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get namespace() {
    return "applications";
  }

  getClaim = async (application_id: string) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "GET",
      application_id
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  /**
   * Fetches the list of claims for a user
   */
  getClaims = async (pageOffset: string | number = 1) => {
    const { data, meta } = await this.request<BenefitsApplication[]>(
      "GET",
      "",
      {
        order_by: "created_at",
        order_direction: "descending",
        page_offset: pageOffset,
      }
    );

    const claims = data.map((claimData) => new BenefitsApplication(claimData));

    return {
      claims: new ApiResourceCollection<BenefitsApplication>(
        "application_id",
        claims
      ),
      paginationMeta: meta?.paging ?? {},
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   */
  completeClaim = async (application_id: string) => {
    const { data } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/complete_application`
    );

    return {
      claim: new BenefitsApplication(data),
    };
  };

  createClaim = async () => {
    const { data } = await this.request<BenefitsApplication>("POST");

    return {
      claim: new BenefitsApplication(data),
    };
  };

  updateClaim = async (
    application_id: string,
    patchData: Partial<BenefitsApplication>
  ) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "PATCH",
      application_id,
      patchData
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  /**
   * Signal data entry for Part 1 is complete and ready
   * to be submitted to the claims processing system.
   */
  submitClaim = async (application_id: string) => {
    const splitClaimsAcrossByEnabled = Boolean(
      isFeatureEnabled("splitClaimsAcrossBY")
    );
    const { data } = await this.request<
      | BenefitsApplication
      | {
          existing_application: BenefitsApplication;
          split_application: BenefitsApplication | null;
        }
    >("POST", `${application_id}/submit_application`, undefined, {
      additionalHeaders: splitClaimsAcrossByEnabled
        ? { "X-FF-Split-Claims-Across-BY": "true" }
        : {},
    });
    // TODO (API-2447)
    // This should get cleaned up as part of completing
    // But is a temporary handler for the API potentially return different shapes
    if ("existing_application" in data) {
      return {
        claim: new BenefitsApplication(data.existing_application),
      };
    }
    return {
      claim: new BenefitsApplication(data),
    };
  };

  submitPaymentPreference = async (
    application_id: string,
    paymentPreferenceData: Partial<PaymentPreference>
  ) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/submit_payment_preference`,
      paymentPreferenceData
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  submitTaxWithholdingPreference = async (
    application_id: string,
    preferenceData: Partial<TaxWithholdingPreference>
  ) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/submit_tax_withholding_preference`,
      preferenceData
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };
}
