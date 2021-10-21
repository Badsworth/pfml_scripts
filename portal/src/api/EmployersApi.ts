import BaseApi, {
  createRequestUrl,
  fetchErrorToNetworkError,
  getAuthorizationHeader,
  handleNotOkResponse,
} from "./BaseApi";
import ClaimDocument from "../models/ClaimDocument";
import DocumentCollection from "../models/DocumentCollection";
import EmployerClaim from "../models/EmployerClaim";
import { UserLeaveAdministrator } from "../models/User";
import Withholding from "../models/Withholding";
import routes from "../routes";

export default class EmployersApi extends BaseApi {
  get basePath() {
    return routes.api.employers;
  }

  get i18nPrefix() {
    return "employers";
  }

  /**
   * Add an FEIN to the logged in Leave Administrator
   */
  addEmployer = async (postData: { employer_fein: string }) => {
    const { data } = await this.request<UserLeaveAdministrator>(
      "POST",
      "add",
      postData
    );
    return new UserLeaveAdministrator(data);
  };

  getClaim = async (absenceId: string) => {
    const { data } = await this.request<EmployerClaim>(
      "GET",
      `claims/${absenceId}/review`
    );

    return {
      claim: new EmployerClaim(data),
    };
  };

  /**
   * @param absenceId of the Claim
   * @param document instance to download
   */
  downloadDocument = async (absenceId: string, document: ClaimDocument) => {
    const { content_type, fineos_document_id } = document;
    const subPath = `/claims/${absenceId}/documents/${fineos_document_id}`;
    const method = "GET";
    const url = createRequestUrl(method, this.basePath, subPath);
    const authHeader = await getAuthorizationHeader();

    const headers = {
      ...authHeader,
      "Content-Type": content_type || "",
    };

    let blob: Blob, response: Response;
    try {
      response = await fetch(url, { headers, method });
      blob = await response.blob();
    } catch (error) {
      throw fetchErrorToNetworkError(error);
    }

    if (!response.ok) {
      handleNotOkResponse(response, [], this.i18nPrefix);
    }

    return blob;
  };

  /**
   * Loads all documents for the provided FINEOS Absence ID
   */
  getDocuments = async (absenceId: string) => {
    const { data } = await this.request<ClaimDocument[]>(
      "GET",
      `claims/${absenceId}/documents`
    );
    const documents = data.map(
      (documentData) => new ClaimDocument(documentData)
    );

    return {
      documents: new DocumentCollection(documents),
    };
  };

  /**
   * Retrieves the date for which the leave admin must search for withholding data from MTC.
   */
  getWithholding = async (employer_id: string) => {
    const { data } = await this.request<Withholding>(
      "GET",
      `withholding/${employer_id}`
    );
    return new Withholding(data);
  };

  submitClaimReview = async (
    absenceId: string,
    patchData: Record<string, unknown>
  ) => {
    await this.request("PATCH", `claims/${absenceId}/review`, patchData);
  };

  /**
   * Submit withholding data for validation
   */
  submitWithholding = async (postData: Record<string, unknown>) => {
    await this.request("POST", "verifications", postData);
  };
}
