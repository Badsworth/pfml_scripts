import { BadRequestError, ValidationError } from "../../src/errors";
import { act, renderHook } from "@testing-library/react-hooks";
import {
  attachDocumentMock,
  downloadDocumentMock,
  getDocumentsMock,
} from "../../src/api/DocumentsApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import { makeFile } from "../test-utils";
import { uniqueId } from "lodash";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useDocumentsLogic from "../../src/hooks/useDocumentsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/DocumentsApi");
jest.mock("../../src/services/tracker");

describe("useDocumentsLogic", () => {
  const application_id = "mock-application-id-1";
  const application_id2 = "mock-application-id-2";
  const mockDocumentType = "Medical Certification";
  const mockFilename = "test_file.png";
  let appErrorsLogic, documentsLogic;

  function setup() {
    renderHook(() => {
      const portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      documentsLogic = useDocumentsLogic({ appErrorsLogic });
    });
  }

  beforeEach(() => {
    setup();
  });

  afterEach(() => {
    appErrorsLogic = null;
    documentsLogic = null;
  });

  it("returns documents as instance of DocumentCollection", () => {
    expect(documentsLogic.documents).toBeInstanceOf(DocumentCollection);
  });

  describe("attach", () => {
    it("returns an array with a promise for each file", async () => {
      const files = [
        { id: "1", file: makeFile({ name: "file1" }) },
        { id: "2", file: makeFile({ name: "file2" }) },
        { id: "3", file: makeFile({ name: "file3" }) },
      ];

      let uploadPromises;

      await act(async () => {
        uploadPromises = await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });

      expect(uploadPromises).toHaveLength(3);
    });

    it("returns promises that resolve with a success=true when the upload success", async () => {
      const files = [{ id: "1", file: makeFile({ name: "file1" }) }];
      attachDocumentMock.mockResolvedValueOnce({
        success: true,
        document: { fineos_document_id: uniqueId() },
      });

      let uploadPromises;

      await act(async () => {
        uploadPromises = await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });

      return expect(uploadPromises[0]).resolves.toEqual({ success: true });
    });

    it("returns promises that resolve with a success=false when the upload fails", async () => {
      const files = [{ id: "1", file: makeFile({ name: "file1" }) }];
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      attachDocumentMock.mockRejectedValueOnce(new Error("upload error"));

      let uploadPromises;

      await act(async () => {
        uploadPromises = await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });

      return expect(uploadPromises[0]).resolves.toEqual({ success: false });
    });

    it("asynchronously submits documents", async () => {
      const files = [
        { id: "1", file: makeFile({ name: "file1" }) },
        { id: "2", file: makeFile({ name: "file2" }) },
        { id: "3", file: makeFile({ name: "file3" }) },
      ];
      await act(async () => {
        await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });

      files.forEach((fileWithUniqueId) => {
        expect(attachDocumentMock).toHaveBeenCalledWith(
          application_id,
          fileWithUniqueId.file,
          mockDocumentType,
          false
        );
      });
    });

    it("submits documents with mark_evidence_received is true", async () => {
      const files = [{ id: "1", file: makeFile({ name: "file1" }) }];
      await act(async () => {
        await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          true
        );
      });

      files.forEach((fileWithUniqueId) => {
        expect(attachDocumentMock).toHaveBeenCalledWith(
          application_id,
          fileWithUniqueId.file,
          mockDocumentType,
          true
        );
      });
    });

    describe("when documents have previously been loaded", () => {
      let newDocument, previouslyLoadedDocuments;

      beforeEach(async () => {
        previouslyLoadedDocuments = new DocumentCollection([
          new Document({ application_id, fineos_document_id: 1 }),
          new Document({ application_id, fineos_document_id: 2 }),
          new Document({ application_id, fineos_document_id: 3 }),
        ]);

        getDocumentsMock.mockImplementationOnce(() => {
          return {
            success: true,
            status: 200,
            documents: previouslyLoadedDocuments,
          };
        });

        // load the documents into documentsLogic
        await act(async () => {
          await documentsLogic.loadAll(application_id);
        });
        // reset the call count
        getDocumentsMock.mockClear();

        newDocument = new Document({
          application_id,
          document_type: mockDocumentType,
          fineos_document_id: 5,
          name: mockFilename,
        });

        attachDocumentMock.mockImplementationOnce(() => {
          return {
            success: true,
            document: newDocument,
          };
        });
      });

      it("stores the newly uploaded document", async () => {
        const files = [{ id: "1", file: makeFile({ name: "file1" }) }];
        let { documents } = documentsLogic;

        expect(documents.items).toHaveLength(3);

        await act(async () => {
          await documentsLogic.attach(
            application_id,
            files,
            mockDocumentType,
            false
          );
        });

        ({ documents } = documentsLogic);
        expect(documents.items).toHaveLength(4);
        expect(documents.items).toContain(newDocument);
      });

      it("doesn't affect existing documents", async () => {
        let { documents } = documentsLogic;
        const files = [makeFile({ name: mockFilename })];
        expect(documents.items).toHaveLength(3);
        await act(async () => {
          await documentsLogic.attach(
            application_id,
            files,
            mockDocumentType,
            false
          );
        });

        ({ documents } = documentsLogic);

        previouslyLoadedDocuments.items.forEach((document) => {
          expect(documents.items).toContain(document);
        });
      });
    });
  });

  describe("when there are errors", () => {
    beforeEach(() => {
      // remove error logs
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    });

    it("throws ValidationError when no files are included in the request", async () => {
      const files = [];
      await act(async () => {
        await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });
      expect(appErrorsLogic.appErrors.items[0]).toEqual(
        expect.objectContaining({
          field: "file",
          message: "Upload at least one file to continue.",
          meta: null,
          name: "ValidationError",
          rule: null,
          type: "required",
        })
      );
    });

    it("updates the app errors, and includes the claim + file ids", async () => {
      attachDocumentMock
        // file1 - success:
        .mockResolvedValueOnce({
          success: true,
          document: new Document({ fineos_document_id: uniqueId() }),
        })
        // file2 - JS exception
        .mockRejectedValueOnce(new Error("File 2 failed"))
        // file3 - fineos error
        .mockRejectedValueOnce(
          new ValidationError([
            {
              field: "",
              message: "FINEOS Client Exception",
              rule: "",
              type: "fineos_client",
            },
          ])
        );

      const files = [
        { id: "1", file: makeFile({ name: "file1" }) },
        { id: "2", file: makeFile({ name: "file2" }) },
        { id: "3", file: makeFile({ name: "file3" }) },
      ];

      await act(async () => {
        await documentsLogic.attach(
          application_id,
          files,
          mockDocumentType,
          false
        );
      });

      const appErrorInfos = appErrorsLogic.appErrors.items;

      expect(appErrorInfos).toHaveLength(2);
      expect(appErrorInfos[0].name).toBe("DocumentsUploadError");
      expect(appErrorInfos[0].meta).toMatchInlineSnapshot(`
        Object {
          "application_id": "mock-application-id-1",
          "file_id": "2",
        }
      `);
      expect(appErrorInfos[0].message).toMatchInlineSnapshot(
        `"We encountered an error when uploading your file. Try uploading your file again. If this continues to happen, call the Contact Center at (833) 344‑7365."`
      );
    });
  });

  it("clears prior errors", async () => {
    act(() => {
      appErrorsLogic.setAppErrors(
        new AppErrorInfoCollection([new AppErrorInfo()])
      );
    });

    attachDocumentMock.mockResolvedValueOnce({
      success: true,
      document: new Document({ fineos_document_id: uniqueId() }),
    }); // file1 - success

    const files = [{ id: "1", file: makeFile({ name: "file1" }) }];
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

    let uploadPromises;

    await act(async () => {
      uploadPromises = await documentsLogic.attach(
        application_id,
        files,
        mockDocumentType,
        false
      );

      await Promise.all(uploadPromises);
    });

    expect(appErrorsLogic.appErrors.items).toHaveLength(0);
  });

  describe("loadAll", () => {
    describe("when the request is successful", () => {
      describe("when the API returns documents", () => {
        let loadedDocuments;
        beforeEach(async () => {
          loadedDocuments = new DocumentCollection([
            new Document({ application_id, fineos_document_id: 1 }),
            new Document({ application_id, fineos_document_id: 2 }),
            new Document({ application_id, fineos_document_id: 3 }),
          ]);

          getDocumentsMock.mockResolvedValueOnce({
            status: 200,
            success: true,
            documents: loadedDocuments,
          });

          await act(async () => {
            await documentsLogic.loadAll(application_id);
          });
        });

        it("asynchronously fetches all documents for an application and adds to documents collection", () => {
          loadedDocuments.items.forEach((document) => {
            expect(documentsLogic.documents.items).toContain(document);
          });
          expect(documentsLogic.documents.items).toHaveLength(
            loadedDocuments.items.length
          );
          expect(getDocumentsMock).toHaveBeenCalledWith(application_id);
        });

        it("only makes an api request if documents have not already been loaded for an application", async () => {
          getDocumentsMock.mockClear();
          await act(async () => {
            await documentsLogic.loadAll(application_id);
          });
          expect(getDocumentsMock).not.toHaveBeenCalled();
        });

        it("merges previously loaded documents with newly loaded documents", async () => {
          const newApplicationId = "mock-application-id-2";
          const newDocuments = new DocumentCollection([
            new Document({
              application_id: newApplicationId,
              fineos_document_id: 4,
            }),
            new Document({
              application_id: newApplicationId,
              fineos_document_id: 5,
            }),
            new Document({
              application_id: newApplicationId,
              fineos_document_id: 6,
            }),
          ]);
          getDocumentsMock.mockResolvedValueOnce({
            success: true,
            status: 200,
            documents: newDocuments,
          });

          await act(async () => {
            await documentsLogic.loadAll(newApplicationId);
          });
          const documents = documentsLogic.documents;
          expect(documents.items).toHaveLength(6);
          newDocuments.items.forEach((document) => {
            expect(documents.items).toContain(document);
          });
        });
      });

      describe("when the API doesn't return documents", () => {
        beforeEach(() => {
          getDocumentsMock.mockResolvedValue({
            status: 200,
            success: true,
            documents: new DocumentCollection([]),
          });
        });

        it("only makes the API request once for the same application", async () => {
          await act(async () => {
            await documentsLogic.loadAll(application_id);
            await documentsLogic.loadAll(application_id);
          });

          expect(getDocumentsMock).toHaveBeenCalledTimes(1);
        });
      });
    });

    describe("when request errors", () => {
      beforeEach(() => {
        // remove error logs
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches the error", async () => {
        getDocumentsMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await documentsLogic.loadAll(application_id);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "DocumentsLoadError"
        );
        expect(appErrorsLogic.appErrors.items[0].meta).toEqual({
          application_id,
        });
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await documentsLogic.loadAll(application_id);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    it("resolves race conditions", async () => {
      let resolveFirstLoad, resolveSecondLoad;

      const documentSet1 = new DocumentCollection([
        new Document({ application_id, fineos_document_id: 1 }),
        new Document({ application_id, fineos_document_id: 2 }),
        new Document({ application_id, fineos_document_id: 3 }),
      ]);

      const documentSet2 = new DocumentCollection([
        new Document({
          application_id: application_id2,
          fineos_document_id: 4,
        }),
        new Document({
          application_id: application_id2,
          fineos_document_id: 5,
        }),
        new Document({
          application_id: application_id2,
          fineos_document_id: 6,
        }),
      ]);

      getDocumentsMock
        .mockImplementationOnce(
          () =>
            new Promise((resolve, reject) => {
              resolveFirstLoad = resolve;
            })
        )
        .mockImplementationOnce(
          () =>
            new Promise((resolve, reject) => {
              resolveSecondLoad = resolve;
            })
        );

      await act(async () => {
        const promise1 = documentsLogic.loadAll(application_id);
        const promise2 = documentsLogic.loadAll(application_id2);
        resolveFirstLoad({
          success: true,
          status: 200,
          documents: documentSet1,
        });
        resolveSecondLoad({
          success: true,
          status: 200,
          documents: documentSet2,
        });
        await promise1;
        await promise2;
      });

      expect(documentsLogic.documents.items).toEqual([
        ...documentSet1.items,
        ...documentSet2.items,
      ]);
    });
  });

  describe("hasLoadedClaimDocuments", () => {
    it("returns false for initial state", () => {
      expect(documentsLogic.hasLoadedClaimDocuments(application_id)).toBe(
        false
      );
    });

    it("returns true after load successfully", async () => {
      getDocumentsMock.mockResolvedValueOnce({
        status: 200,
        success: true,
        documents: new DocumentCollection([
          new Document({ application_id, fineos_document_id: 1 }),
        ]),
      });

      await act(async () => {
        await documentsLogic.loadAll(application_id);
      });

      expect(documentsLogic.hasLoadedClaimDocuments(application_id)).toBe(true);
    });

    it("returns true when there are no documents for an application", async () => {
      getDocumentsMock.mockResolvedValueOnce({
        status: 200,
        success: true,
        documents: new DocumentCollection([]),
      });

      await act(async () => {
        await documentsLogic.loadAll(application_id);
      });

      expect(documentsLogic.hasLoadedClaimDocuments(application_id)).toBe(true);
    });
  });

  describe("download", () => {
    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      const document = new Document({
        application_id,
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      await act(async () => {
        await documentsLogic.download(document);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    it("makes a request to the API", () => {
      const document = new Document({
        application_id,
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      act(() => {
        documentsLogic.download(document);
      });

      expect(downloadDocumentMock).toHaveBeenCalledWith(document);
    });

    it("returns a blob", async () => {
      const document = new Document({
        application_id,
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      let response;
      await act(async () => {
        response = await documentsLogic.download(document);
      });

      expect(response).toBeInstanceOf(Blob);
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

      downloadDocumentMock.mockImplementationOnce(() => {
        throw new BadRequestError();
      });

      await act(async () => {
        await documentsLogic.download();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toEqual("BadRequestError");
    });
  });
});
