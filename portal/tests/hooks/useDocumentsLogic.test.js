import {
  attachDocumentsMock,
  getDocumentsMock,
} from "../../src/api/DocumentsApi";
import { makeFile, testHook } from "../test-utils";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import { act } from "react-dom/test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useDocumentsLogic from "../../src/hooks/useDocumentsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/DocumentsApi");

describe("useDocumentsLogic", () => {
  const application_id = "mock-application-id-1";
  const application_id2 = "mock-application-id-2";
  const mockDocumentType = "Medical Certification";
  let appErrorsLogic, documentsLogic, portalFlow;

  function renderHook() {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
      portalFlow = usePortalFlow();
      documentsLogic = useDocumentsLogic({ appErrorsLogic, portalFlow });
    });
  }

  beforeEach(() => {
    renderHook();
  });

  afterEach(() => {
    appErrorsLogic = null;
    documentsLogic = null;
    portalFlow = null;
  });

  it("returns documents as instance of DocumentCollection", () => {
    expect(documentsLogic.documents).toBeInstanceOf(DocumentCollection);
  });

  describe("attach", () => {
    it("asynchronously submits documents", async () => {
      const files = [makeFile(), makeFile(), makeFile()];
      await act(async () => {
        await documentsLogic.attach(application_id, files, mockDocumentType);
      });

      expect(attachDocumentsMock).toHaveBeenCalledWith(
        application_id,
        files,
        mockDocumentType
      );
    });

    describe("when the request is successful", () => {
      const mockDocumentType = "Medical Certification";
      const mockFilename = "testUploadImage.jpg";
      let files;

      it("redirects to nextPage", async () => {
        const spy = jest.spyOn(portalFlow, "goToNextPage");
        await act(async () => {
          await documentsLogic.attach(application_id, files, mockDocumentType);
        });
        expect(spy).toHaveBeenCalled();
      });

      describe("when documents have not been previously loaded", () => {
        const newDocument = new Document({
          application_id,
          document_type: mockDocumentType,
          fineos_document_id: 1,
          name: mockFilename,
        });

        beforeEach(() => {
          files = [makeFile({ name: mockFilename })];

          getDocumentsMock.mockResolvedValueOnce({
            status: 200,
            success: true,
            documents: new DocumentCollection([newDocument]),
          });
        });

        it("calls documentsApi.getDocuments", async () => {
          await act(async () => {
            await documentsLogic.attach(
              application_id,
              files,
              mockDocumentType
            );
          });

          expect(getDocumentsMock).toHaveBeenCalledTimes(1);
        });

        it("updates documentsLogic.documents with the new document", async () => {
          await act(async () => {
            await documentsLogic.attach(
              application_id,
              files,
              mockDocumentType
            );
          });

          const { documents } = documentsLogic;

          expect(documents.items).toHaveLength(1);
          expect(documents.items).toContain(newDocument);
        });
      });

      describe("when documents have previously been loaded", () => {
        let files, newDocument, previouslyLoadedDocuments;

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
            await documentsLogic.load(application_id);
          });
          // reset the call count
          getDocumentsMock.mockClear();

          newDocument = new Document({
            application_id,
            document_type: mockDocumentType,
            fineos_document_id: 5,
            name: mockFilename,
          });
          files = [makeFile({ name: mockFilename })];

          attachDocumentsMock.mockImplementationOnce(() => {
            return {
              success: true,
              document: newDocument,
            };
          });
        });

        it("should not call documentsApi.getDocuments", async () => {
          await act(async () => {
            await documentsLogic.attach(
              application_id,
              files,
              mockDocumentType
            );
          });

          expect(getDocumentsMock).not.toHaveBeenCalled();
        });

        it("stores the new document", async () => {
          let { documents } = documentsLogic;

          expect(documents.items).toHaveLength(3);
          await act(async () => {
            await documentsLogic.attach(
              application_id,
              files,
              mockDocumentType
            );
          });

          ({ documents } = documentsLogic);
          expect(documents.items).toHaveLength(4);
          expect(documents.items).toContain(newDocument);
        });

        it("doesn't affect existing documents", async () => {
          let { documents } = documentsLogic;

          expect(documents.items).toHaveLength(3);
          await act(async () => {
            await documentsLogic.attach(
              application_id,
              files,
              mockDocumentType
            );
          });

          ({ documents } = documentsLogic);

          previouslyLoadedDocuments.items.forEach((document) => {
            expect(documents.items).toContain(document);
          });
        });
      });
    });

    describe("when request errors", () => {
      beforeEach(() => {
        // remove error logs
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches the error", async () => {
        attachDocumentsMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          const files = [makeFile(), makeFile(), makeFile()];
          await documentsLogic.attach(application_id, files, mockDocumentType);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await documentsLogic.load(application_id);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });

  describe("load", () => {
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
            await documentsLogic.load(application_id);
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
            await documentsLogic.load(application_id);
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
            await documentsLogic.load(newApplicationId);
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
            await documentsLogic.load(application_id);
            await documentsLogic.load(application_id);
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
          await documentsLogic.load(application_id);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await documentsLogic.load(application_id);
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
        const promise1 = documentsLogic.load(application_id);
        const promise2 = documentsLogic.load(application_id2);
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
        await documentsLogic.load(application_id);
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
        await documentsLogic.load(application_id);
      });

      expect(documentsLogic.hasLoadedClaimDocuments(application_id)).toBe(true);
    });
  });
});
