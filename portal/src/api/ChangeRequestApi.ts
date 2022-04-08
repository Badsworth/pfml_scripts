import {
  BenefitsApplicationDocument,
  DocumentTypeEnum,
} from "src/models/Document";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import BaseApi from "./BaseApi";
import { ChangeRequest } from "src/models/ChangeRequest";
import { getDocumentFormData } from "./DocumentsApi";
import routes from "src/routes";

export default class ChangeRequestApi extends BaseApi {
  get basePath(): string {
    return routes.api.changeRequest;
  }

  get namespace(): string {
    return "change_request";
  }

  getChangeRequests = async (absence_case_id: string) => {
    const { data } = await this.request<ChangeRequest[]>("GET", undefined, {
      fineos_absence_id: absence_case_id,
    });

    return {
      changeRequests: new ApiResourceCollection<ChangeRequest>(
        "change_request_id",
        data
      ),
    };
  };

  createChangeRequest = async (absence_case_id: string) => {
    const { data } = await this.request<ChangeRequest>(
      "POST",
      `?fineos_absence_id=${absence_case_id}`
    );

    return { changeRequest: new ChangeRequest(data) };
  };

  deleteChangeRequest = async (change_request_id: string) => {
    const { data } = await this.request<ChangeRequest>(
      "DELETE",
      change_request_id
    );

    return { changeRequest: new ChangeRequest(data) };
  };

  updateChangeRequest = async (
    change_request_id: string,
    patchData: Partial<ChangeRequest>
  ) => {
    const { data, warnings } = await this.request<ChangeRequest>(
      "PATCH",
      change_request_id,
      patchData
    );

    return {
      changeRequest: new ChangeRequest(data),
      warnings,
    };
  };

  submitChangeRequest = async (change_request_id: string) => {
    const { data, warnings } = await this.request<ChangeRequest>(
      "POST",
      `${change_request_id}/submit`
    );

    return {
      changeRequest: new ChangeRequest(data),
      warnings,
    };
  };

  attachChangeRequestDocument = async (
    change_request_id: string,
    file: File,
    document_type: DocumentTypeEnum
  ) => {
    const formData = getDocumentFormData(file, document_type, true);

    const { data } = await this.request<BenefitsApplicationDocument>(
      "POST",
      `${change_request_id}/documents`,
      formData,
      { multipartForm: true }
    );

    return {
      document: data,
    };
  };
}
