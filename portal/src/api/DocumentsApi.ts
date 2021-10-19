import BaseApi, {
  createRequestUrl,
  getAuthorizationHeader,
  handleError,
  handleNotOkResponse,
} from "./BaseApi";
import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import DocumentCollection from "../models/DocumentCollection";
import { DocumentTypeEnum } from "../models/Document";
import assert from "assert";
import routes from "../routes";

export default class DocumentsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get i18nPrefix() {
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
    // @ts-expect-error ts(2345): Argument of type 'boolean' is not assignable to parameter of type 'string | Blob'.
    // Resolving this TypeScript error **might** require a corresponding change to the OpenAPI schema and API logic.
    formData.append("mark_evidence_received", mark_evidence_received);

    const { data } = await this.request<BenefitsApplicationDocument>(
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
   */
  getDocuments = async (application_id: string) => {
    const { data } = await this.request<BenefitsApplicationDocument[]>(
      "GET",
      `${application_id}/documents`
    );
    const documents = data.map(
      (documentData) => new BenefitsApplicationDocument(documentData)
    );

    return {
      documents: new DocumentCollection(documents),
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
      "Content-Type": content_type,
    };

    let blob: Blob, response: Response;
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
