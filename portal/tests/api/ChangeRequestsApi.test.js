import { makeFile, mockAuth, mockFetch } from "../test-utils";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import ChangeRequest from "../../src/models/ChangeRequest";
import ChangeRequestsApi from "../../src/api/ChangeRequestsApi";
import { ValidationError } from "../../src/errors";

jest.mock("../../src/services/tracker");

describe(ChangeRequestsApi, () => {
  let changeRequestsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const baseRequestHeaders = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    mockAuth(true, accessTokenJwt);
    changeRequestsApi = new ChangeRequestsApi();
  });

  describe("getChangeRequests", () => {
    let changeRequest;

    beforeEach(() => {
      changeRequest = new ChangeRequest({
        change_request_id: "change-request-id",
      });
      global.fetch = mockFetch({
        response: {
          data: [changeRequest],
        },
      });
    });

    it("sends GET request to /change-request?fineos_absence_id=:fineos_absence_id", async () => {
      await changeRequestsApi.getChangeRequests(
        changeRequest.fineos_absence_id
      );
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request?fineos_absence_id=${changeRequest.fineos_absence_id}`,
        {
          body: null,
          headers: baseRequestHeaders,
          method: "GET",
        }
      );
    });

    it("resolves with change request collection", async () => {
      const { changeRequests: changeRequestResponse } =
        await changeRequestsApi.getChangeRequests(
          changeRequest.fineos_absence_id
        );

      expect(changeRequestResponse).toEqual(
        new ApiResourceCollection("change_request_id", [changeRequest])
      );
    });
  });

  describe("createChangeRequest", () => {
    describe("on successful request", () => {
      let changeRequest;

      beforeEach(() => {
        changeRequest = new ChangeRequest({
          change_request_id: "change-request-id",
        });
        global.fetch = mockFetch({
          response: {
            data: changeRequest,
          },
          status: 201,
        });
      });

      it("sends POST request to /change-request/?fineos_absence_id=:fineos_absence_id", async () => {
        await changeRequestsApi.createChangeRequest(
          changeRequest.fineos_absence_id
        );
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/change-request/?fineos_absence_id=${changeRequest.fineos_absence_id}`,
          {
            body: null,
            headers: baseRequestHeaders,
            method: "POST",
          }
        );
      });

      it("resolves with change request properties", async () => {
        const { changeRequest: changeRequestResponse } =
          await changeRequestsApi.createChangeRequest(
            changeRequest.fineos_absence_id
          );

        expect(changeRequestResponse).toEqual(changeRequest);
      });
    });

    describe("unsucessful request", () => {
      it("throws error", async () => {
        global.fetch = mockFetch({
          response: { data: null, errors: [{ type: "invalid" }] },
          status: 400,
        });

        try {
          await changeRequestsApi.createChangeRequest("fineos-absence-id");
        } catch (error) {
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues[0].namespace).toBe("change_request");
        }
      });
    });
  });

  describe("deleteChangeRequest", () => {
    describe("on successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: {},
          },
          status: 200,
        });
      });

      it("sends DELETE request to /change-request/:change-request-id", async () => {
        const changeRequestId = "change-request-id";
        await changeRequestsApi.deleteChangeRequest(changeRequestId);
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/change-request/${changeRequestId}`,
          {
            body: null,
            headers: baseRequestHeaders,
            method: "DELETE",
          }
        );
      });
    });

    describe("unsucessful request", () => {
      it("throws error", async () => {
        global.fetch = mockFetch({
          response: { data: null, errors: [{ type: "invalid" }] },
          status: 400,
        });

        try {
          await changeRequestsApi.createChangeRequest("fineos-absence-id");
        } catch (error) {
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues[0].namespace).toBe("change_request");
        }
      });
    });
  });

  describe("updateChangeRequest", () => {
    let changeRequest;

    beforeEach(() => {
      changeRequest = new ChangeRequest({
        fineos_absence_id: "fineos-absence-id",
        change_request_id: "change-request-id",
      });
      global.fetch = mockFetch({
        response: {
          data: changeRequest,
          warnings: [
            {
              field: "a",
              type: "b",
              message: "c",
            },
          ],
        },
      });
    });

    it("sends PATCH request to /change-request/:change-request-id", async () => {
      await changeRequestsApi.updateChangeRequest(
        changeRequest.change_request_id,
        changeRequest
      );

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/${changeRequest.change_request_id}`,
        {
          body: JSON.stringify(changeRequest),
          headers: baseRequestHeaders,
          method: "PATCH",
        }
      );
    });

    it("response resolves with change request and warnings", async () => {
      const { changeRequest: changeRequestResponse, warnings } =
        await changeRequestsApi.updateChangeRequest(
          changeRequest.change_request_id,
          changeRequest
        );

      expect(changeRequestResponse).toEqual(changeRequest);
      expect(warnings).toMatchInlineSnapshot(`
        [
          {
            "field": "a",
            "message": "c",
            "namespace": "change_request",
            "type": "b",
          },
        ]
      `);
    });
  });

  describe("submitChangeRequest", () => {
    let changeRequest;

    beforeEach(() => {
      changeRequest = new ChangeRequest({
        fineos_absence_id: "fineos-absence-id",
        change_request_id: "change-request-id",
        start_date: "2022-01-01",
        end_date: "2022-02-01",
        change_request_type: "Modification",
      });
      global.fetch = mockFetch({
        response: { data: changeRequest },
        status: 200,
      });
    });

    it("sends POST request to /change-request/:change-request-id/submit", async () => {
      await changeRequestsApi.submitChangeRequest(
        changeRequest.change_request_id
      );

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/change-request/${changeRequest.change_request_id}/submit`,
        {
          body: null,
          headers: baseRequestHeaders,
          method: "POST",
        }
      );
    });

    it("responds with change request", async () => {
      const { changeRequest: changeRequestResponse } =
        await changeRequestsApi.submitChangeRequest(
          changeRequest.change_request_id
        );

      expect(changeRequestResponse).toEqual(changeRequest);
    });
  });

  describe("", () => {
    const changeRequestId = "change-request-id";
    beforeEach(() => {
      global.fetch = mockFetch({
        response: {
          data: {
            application_id: "application-id",
            fineos_document_id: 1,
          },
        },
        status: 200,
      });
    });

    it("sends POST request to /change-request/:change-request-id/documents", async () => {
      const file = makeFile();

      await changeRequestsApi.attachDocument(
        changeRequestId,
        file,
        "Child bonding evidence form"
      );

      const [url, request] = fetch.mock.calls[0];

      expect(url).toBe(
        `${process.env.apiUrl}/change-request/${changeRequestId}/documents`
      );
      expect(request.method).toBe("POST");
      expect(request.body.get("file")).toBeInstanceOf(File);
      expect(request.body.get("name")).toBe(file.name);
      expect(request.body.get("document_type")).toBe(
        "Child bonding evidence form"
      );
      expect(request.body.get("mark_evidence_received")).toBe("true");
      expect(request.body.get("description")).toBe(null);
    });

    it("resolves with document instance", async () => {
      const file = makeFile();

      const { document: documentResponse } =
        await changeRequestsApi.attachDocument(
          changeRequestId,
          file,
          "Child bonding evidence form"
        );
      expect(documentResponse).toMatchInlineSnapshot(`
        {
          "application_id": "application-id",
          "fineos_document_id": 1,
        }
      `);
    });
  });
});
