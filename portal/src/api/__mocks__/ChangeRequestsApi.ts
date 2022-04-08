import ApiResourceCollection from "../../models/ApiResourceCollection";
import ChangeRequest from "../../models/ChangeRequest";
import { DocumentType } from "src/models/Document";
import { uniqueId } from "lodash";

export const createChangeRequestMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 201,
    changeRequest: new ChangeRequest({
      change_request_id: "change-request-id",
      fineos_absence_id: "fineos-absence-id",
    }),
    warnings: [],
  })
);

export const getChangeRequestsMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 200,
    changeRequests: new ApiResourceCollection("change_request_id", [
      new ChangeRequest({
        change_request_id: "change-request-id",
        fineos_absence_id: "fineos-absence-id",
      }),
    ]),
  })
);

export const updateChangeRequestMock = jest.fn((change_request_id, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
    changeRequest: new ChangeRequest({
      change_request_id,
      fineos_absence_id: "fineos-absence-id",
      ...patchData,
    }),
    warnings: [],
  })
);

export const deleteChangeRequestMock = jest.fn((change_request_id, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
    changeRequest: new ChangeRequest({
      change_request_id,
      fineos_absence_id: "fineos-absence-id",
      ...patchData,
    }),
    warnings: [],
  })
);

export const submitChangeRequestMock = jest.fn((change_request_id) =>
  Promise.resolve({
    success: true,
    status: 201,
    changeRequest: new ChangeRequest({
      change_request_id,
      fineos_absence_id: "fineos-absence-id",
    }),
    warnings: [],
  })
);

export const attachChangeRequestDocumentMock = jest.fn(() => {
  return Promise.resolve({
    success: true,
    status: 200,
    document: {
      content_type: "",
      created_at: "2021-1-1",
      description: "",
      name: "mock doc",
      user_id: "mock-user-id",
      document_type: DocumentType.approvalNotice,
      application_id: "application-id",
      fineos_document_id: uniqueId(),
    },
  });
});

const changeRequestsApi = jest.fn().mockImplementation(() => ({
  submitChangeRequest: submitChangeRequestMock,
  createChangeRequest: createChangeRequestMock,
  getChangeRequests: getChangeRequestsMock,
  updateChangeRequest: updateChangeRequestMock,
  deleteChangeRequest: deleteChangeRequestMock,
  attachChangeRequestDocument: attachChangeRequestDocumentMock,
}));

export default changeRequestsApi;
