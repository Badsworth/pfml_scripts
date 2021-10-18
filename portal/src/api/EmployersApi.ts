import BaseApi, {
  createRequestUrl,
  getAuthorizationHeader,
  handleError,
  handleNotOkResponse,
} from "./BaseApi";
import ClaimDocument from "../models/ClaimDocument";
import DocumentCollection from "../models/DocumentCollection";
import EmployerClaim from "../models/EmployerClaim";
import { UserLeaveAdministrator } from "../models/User";
import Withholding from "../models/Withholding";
import routes from "../routes";

/**
 * @typedef {object} EmployersAPISingleResult
 * @property {EmployerClaim} [claim] - If the request succeeded, this will contain a claim
 */

/**
 * @typedef {object} DocumentApiListResult
 * @property {DocumentCollection} [documents] - If the request succeeded, this will contain a list of documents
 */

export default class EmployersApi extends BaseApi {
  get basePath() {
    return routes.api.employers;
  }

  get i18nPrefix() {
    return "employers";
  }

  /**
   * Add an FEIN to the logged in Leave Administrator
   *
   * @param {object} postData - POST data (FEIN only)
   * @returns {Promise}
   */
  addEmployer = async (postData) => {
    const { data } = await this.request("POST", "add", postData);
    return new UserLeaveAdministrator(data);
  };

  /**
   * Retrieve a claim
   *
   * @param {string} absenceId - FINEOS absence id
   * @returns {Promise<EmployersAPISingleResult>}
   */
  getClaim = async (absenceId) => {
    const { data } = await this.request("GET", `claims/${absenceId}/review`);

    return {
      claim: new EmployerClaim(data),
    };
  };

  /**
   * Download document
   *
   * @param {string} absenceId of the Claim
   * @param {ClaimDocument} document instance of ClaimDocument to download
   * @returns {Blob} file data
   */
  downloadDocument = async (absenceId, document) => {
    const { content_type, fineos_document_id } = document;
    const subPath = `/claims/${absenceId}/documents/${fineos_document_id}`;
    const method = "GET";
    const url = createRequestUrl(method, this.basePath, subPath);
    const authHeader = await getAuthorizationHeader();

    const headers = {
      ...authHeader,
      "Content-Type": content_type,
    };

    let blob, response;
    try {
      response = await fetch(url, { headers, method });
      blob = await response.blob();
    } catch (error) {
      handleError(error);
    }

    if (!response.ok) {
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 5 arguments, but got 2.
      handleNotOkResponse(url, response);
    }

    return blob;
  };

  /**
   * Loads all documents for the provided FINEOS Absence ID
   *
   * Corresponds to this API endpoint: /employers/claims/{fineos_absence_id}/documents
   * @param {string} absenceId ID of the Claim
   * @returns {DocumentApiListResult} The result of the API call
   */
  getDocuments = async (absenceId) => {
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
   * @param {string} employer_id - the ID of the employer to fetch the data for
   * @returns {Promise}
   */
  getWithholding = async (employer_id) => {
    const { data } = await this.request("GET", `withholding/${employer_id}`);
    return new Withholding(data);
  };

  /**
   * Submit an employer claim review
   *
   * @param {string} absenceId - FINEOS absence id
   * @param {object} patchData - PATCH data of amendment and comment fields
   * @returns {Promise}
   */
  submitClaimReview = async (absenceId, patchData) => {
    await this.request("PATCH", `claims/${absenceId}/review`, patchData);
  };

  /**
   * Submit withholding amount for validation
   *
   * @param {object} postData - POST data (includes email, employer id, withholding amount & quarter)
   * @returns {Promise<UserLeaveAdministrator>}
   */
  submitWithholding = async (postData) => {
    await this.request("POST", "verifications", postData);
  };
}
