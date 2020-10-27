import { Auth } from "@aws-amplify/auth";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import DocumentsApi from "../../src/api/DocumentsApi";
import { makeFile } from "../test-utils";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/services/tracker");

const mockFetch = ({
  response = { data: [], errors: [], warnings: [] },
  ok = true,
  status = 200,
}) => {
  return jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok,
    status,
  });
};

describe("DocumentsApi", () => {
  /** @type {DocumentsApi} */
  let documentsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const applicationId = "2a340cf8-6d2a-4f82-a075-73588d003f8f";
  const headers = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    documentsApi = new DocumentsApi();
  });

  describe("attachDocument", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: {
              application_id: applicationId,
              fineos_document_id: 1,
            },
          },
          status: 200,
          ok: true,
        });
      });

      it("sends POST request to /applications/{application_id}/documents", async () => {
        const file = makeFile();

        await documentsApi.attachDocument(applicationId, file, "Mock Category");

        expect(fetch).toHaveBeenCalledTimes(1);

        const [url, request] = fetch.mock.calls[0];

        expect(url).toBe(
          `${process.env.apiUrl}/applications/${applicationId}/documents`
        );
        expect(request.method).toBe("POST");
        expect(request.body.get("file")).toBeInstanceOf(File);
        expect(request.body.get("name")).toBe(file.name);
        expect(request.body.get("document_type")).toBe("Mock Category");
      });

      it("resolves with success, status, and document instance", async () => {
        const file = makeFile();

        const {
          document: documentResponse,
          ...rest
        } = await documentsApi.attachDocument(
          applicationId,
          file,
          "Mock Category"
        );
        expect(documentResponse).toBeInstanceOf(Document);
        expect(rest).toMatchInlineSnapshot(`
          Object {
            "status": 200,
            "success": true,
          }
        `);
      });
    });

    describe("getDocuments", () => {
      describe("successful request", () => {
        beforeEach(() => {
          global.fetch = mockFetch({
            response: {
              data: [
                {
                  application_id: applicationId,
                  fineos_document_id: 1,
                },
                {
                  application_id: applicationId,
                  fineos_document_id: 2,
                },
                {
                  application_id: applicationId,
                  fineos_document_id: 3,
                },
              ],
            },
            status: 200,
            ok: true,
          });
        });

        it("sends GET request to /applications/{application_id/documents", async () => {
          await documentsApi.getDocuments(applicationId);
          expect(fetch).toHaveBeenCalledWith(
            `${process.env.apiUrl}/applications/${applicationId}/documents`,
            {
              body: null,
              headers,
              method: "GET",
            }
          );
        });

        it("resolves with success, status, and DocumentCollection instance", async () => {
          const result = await documentsApi.getDocuments(applicationId);
          expect(result).toEqual({
            documents: expect.any(DocumentCollection),
            status: 200,
            success: true,
          });
          expect(result.documents.items).toEqual([
            new Document({
              application_id: applicationId,
              fineos_document_id: 1,
            }),
            new Document({
              application_id: applicationId,
              fineos_document_id: 2,
            }),
            new Document({
              application_id: applicationId,
              fineos_document_id: 3,
            }),
          ]);
        });
      });
    });
  });
});
