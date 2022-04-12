import BaseApi, {
  createRequestUrl,
  fetchErrorToNetworkError,
  getAuthorizationHeader,
  handleNotOkResponse,
} from "./BaseApi";
import {
  BenefitsApplicationDocument,
  DocumentTypeEnum,
} from "../models/Document";
import ApiResourceCollection from "../models/ApiResourceCollection";
import assert from "assert";
import getDocumentFormData from "../utils/getDocumentFormData";
import routes from "../routes";
export default class DocumentsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get namespace() {
    return "documents";
  }

  /**
   * @param mark_evidence_received - Set the flag used to indicate whether
   * the doc is ready for review or not. Docs added to a claim that was completed
   * through a channel other than the Portal require this flag being set to `true`.
   */
  attachDocument = async (
    application_id: string,
    file: File,
    document_type: DocumentTypeEnum,
    mark_evidence_received: boolean
  ) => {
    const formData = getDocumentFormData(
      file,
      document_type,
      mark_evidence_received
    );

    const { data } = await this.request<BenefitsApplicationDocument>(
      "POST",
      `${application_id}/documents`,
      formData,
      { multipartForm: true }
    );

    return {
      document: data,
    };
  };

  /**
   * Load all documents for an application
   */
  getDocuments = async (application_id: string) => {
    const { data } = await this.request<BenefitsApplicationDocument[]>(
      "GET",
      `${application_id}/documents`
    );

    return {
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        data
      ),
    };
  };

  /**
   * @param document instance of BenefitsApplicationDocument to download
   */
  downloadDocument = async (document: BenefitsApplicationDocument) => {
    assert(document);
    const { application_id, content_type, fineos_document_id } = document;
    const subPath = `${application_id}/documents/${fineos_document_id}`;
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
      handleNotOkResponse(response, [], this.namespace);
    }

    return blob;
  };
}
