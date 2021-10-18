import BaseApi, {
  createRequestUrl,
  getAuthorizationHeader,
  handleError,
  handleNotOkResponse,
} from "./BaseApi";
import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import DocumentCollection from "../models/DocumentCollection";
import assert from "assert";
import routes from "../routes";

/**
 * @typedef {object} DocumentApiSingleResult
 * @property {BenefitsApplicationDocument} document - If the request succeeded, this will contain the created claim
 */

/**
 * @typedef {object} DocumentApiListResult
 * @property {DocumentCollection} [documents] - If the request succeeded, this will contain a list of documents
 */

/**
 * @typedef {{ blob: Blob }} DocumentResponse
 * @property {Blob} blob - BenefitsApplicationDocument data
 */

export default class DocumentsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get i18nPrefix() {
    return "documents";
  }

  /**
   * Submit documents one at a time
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents
   * @param {string} application_id ID of the Claim
   * @param {File} file - The File object to upload
   * @param {string} document_type type of documents
   * @param {boolean} mark_evidence_received - Set the flag used to indicate whether
   * the doc is ready for review or not. Docs added to a claim that was completed
   * through a channel other than the Portal require this flag being set to `true`.
   * @returns {DocumentApiSingleResult} The result of the API call
   */
  attachDocument = async (
    application_id,
    file,
    document_type,
    mark_evidence_received
  ) => {
    const formData = new FormData();
    formData.append("document_type", document_type);
    if (file.name.includes("Compressed_")) {
      formData.append("description", "Compressed Image");
    }

    assert(file);
    // we use Blob to support IE 11, formData is using "blob" as the default file name,
    // so we pass the actual file name here
    // https://developer.mozilla.org/en-US/docs/Web/API/FormData/append#append_parameters
    formData.append("file", file, file.name);
    formData.append("name", file.name);
    formData.append("mark_evidence_received", mark_evidence_received);

    const { data } = await this.request(
      "POST",
      `${application_id}/documents`,
      formData,
      null,
      { multipartForm: true }
    );

    return {
      document: new BenefitsApplicationDocument(data),
    };
  };

  /**
   * Load all documents for an application
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents
   * @param {string} application_id ID of the Claim
   * @returns {DocumentApiListResult} The result of the API call
   */
  getDocuments = async (application_id) => {
    const { data } = await this.request("GET", `${application_id}/documents`);
    let documents = data.map(
      (documentData) => new BenefitsApplicationDocument(documentData)
    );
    documents = new DocumentCollection(documents);

    return {
      documents,
    };
  };

  /**
   * Download document
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents/{fineos_document_id}
   * @param {BenefitsApplicationDocument} document instance of BenefitsApplicationDocument to download
   * @returns {Blob} file data
   */
  downloadDocument = async (document) => {
    assert(document);
    const { application_id, content_type, fineos_document_id } = document;
    const subPath = `${application_id}/documents/${fineos_document_id}`;
    const method = "GET";
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 4 arguments, but got 3.
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
}
