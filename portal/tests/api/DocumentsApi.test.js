import { Auth } from "@aws-amplify/auth";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import DocumentsApi from "../../src/api/DocumentsApi";
import { makeFile } from "../test-utils";

jest.mock("@aws-amplify/auth");

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
    let files;
    describe("successful request", () => {
      beforeEach(() => {
        files = [
          { file: makeFile() },
          { file: makeFile() },
          { file: makeFile() },
        ];
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
        await documentsApi.attachDocuments(
          applicationId,
          files,
          "Mock Category"
        );
        const formData = new FormData();
        formData.append("document_type", "Certification");
        formData.append("file", files[0].file);
        formData.append("name", files[0].file.name);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/applications/${applicationId}/documents`,
          expect.objectContaining({
            body: formData,
            headers: { Authorization: `Bearer ${accessTokenJwt}` },
            method: "POST",
          })
        );
      });

      it("resolves with success, status, and document instance", async () => {
        const {
          document: documentResponse,
          ...rest
        } = await documentsApi.attachDocuments(
          applicationId,
          files,
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
