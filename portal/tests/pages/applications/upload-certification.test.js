import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import TempFile from "../../../src/models/TempFile";
import TempFileCollection from "../../../src/models/TempFileCollection";
import UploadCertification from "../../../src/pages/applications/upload-certification";
import { ValidationError } from "../../../src/errors";
import { act } from "react-dom/test-utils";
import { uniqueId } from "lodash";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");
jest.mock("../../../src/services/tracker");

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

const makeTempFile = (fileAttrs = {}) =>
  new TempFile({ file: makeFile(fileAttrs) });

describe("UploadCertification", () => {
  let appLogic, claim, wrapper;

  describe("before any documents have been loaded", () => {
    function render() {
      ({ appLogic, wrapper } = renderWithAppLogic(UploadCertification, {
        claimAttrs: claim,
        diveLevels,
      }));
    }

    beforeEach(() => {
      claim = new MockClaimBuilder().medicalLeaveReason().create();
      render();
    });

    it("does not render a FileCardList", () => {
      expect(wrapper.exists("FileCardList")).toBe(false);
    });

    it("renders a spinner", () => {
      expect(wrapper.find("Spinner")).toHaveLength(1);
    });

    it("does not render the ReviewRow block", () => {
      expect(wrapper.find("ReviewRow")).toEqual({});
    });
  });

  describe("after documents have been loaded", () => {
    function render(attrs = {}) {
      ({ wrapper } = renderWithAppLogic(UploadCertification, {
        claimAttrs: claim,
        diveLevels,
        props: { appLogic },
      }));
    }

    const expectedTempFiles = [
      expect.objectContaining({
        file: expect.objectContaining({ name: "file1" }),
      }),
      expect.objectContaining({
        file: expect.objectContaining({ name: "file2" }),
      }),
    ];

    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
        jest
          .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
          .mockImplementation(() => {
            return true;
          });
      });
    });

    describe("when the claim has been completed", () => {
      it("redirects to the Applications page when the claim has been completed", async () => {
        claim = new MockClaimBuilder().completed().create();
        appLogic.claims.claims = new ClaimCollection([claim]);
        render();

        // Add files to the page state
        const files = [makeFile(), makeFile()];
        const input = wrapper.find("FileCardList").dive().find("input");
        act(() => {
          input.simulate("change", {
            target: {
              files,
            },
          });
        });

        await act(async () => {
          await wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
          { claim },
          {
            claim_id: claim.application_id,
            uploadedAbsenceId: claim.fineos_absence_id,
          }
        );
      });
    });

    describe("when leave reason is Medical leave", () => {
      beforeEach(() => {
        claim = new MockClaimBuilder().medicalLeaveReason().create();
        appLogic.claims.claims = new ClaimCollection([claim]);
      });

      it("renders a FileCardList", () => {
        render();
        expect(wrapper.find("FileCardList")).toHaveLength(1);
        expect(wrapper.find("FileCardList")).toMatchSnapshot();
      });

      it("doesn't render a spinner", () => {
        render();
        expect(wrapper.find("Spinner")).toEqual({});
      });

      it("renders page with medical leave content", () => {
        render();
        // Only take snapshots of the i18n content
        expect(wrapper.find("Heading")).toMatchSnapshot();
        expect(wrapper.find("Trans").dive()).toMatchSnapshot();
      });

      describe("when the user uploads files", () => {
        let tempFiles;
        beforeEach(() => {
          tempFiles = [makeTempFile(), makeTempFile(), makeTempFile()];
          render();

          wrapper.find("FileCardList").simulate("addTempFiles", tempFiles);
        });

        it("passes files to FileCardList as a TempFileCollection", () => {
          const tempFilesProp = wrapper.find("FileCardList").prop("tempFiles");
          expect(tempFilesProp).toBeInstanceOf(TempFileCollection);
          expect(tempFilesProp.items).toHaveLength(3);
        });

        it("clears errors", () => {
          expect(appLogic.clearErrors).toHaveBeenCalledTimes(1);
        });

        it("catches invalid errors from onInvalidFilesError", () => {
          render();
          act(() => {
            wrapper
              .find("FileCardList")
              .simulate(
                "invalidFilesError",
                new ValidationError([{ message: "Validation message" }])
              );
          });

          const error = appLogic.catchError.mock.calls[0][0];
          expect(error).toBeInstanceOf(ValidationError);
          expect(error.issues).toMatchInlineSnapshot(`
            Array [
              Object {
                "message": "Validation message",
              },
            ]
          `);
        });

        it("makes API request when no documents exist", async () => {
          claim = new MockClaimBuilder().create();
          render();

          // Add files to the page state
          const tempFiles = [
            makeTempFile({ name: "file1" }),
            makeTempFile({ name: "file2" }),
          ];

          act(() => {
            wrapper.find("FileCardList").simulate("addTempFiles", tempFiles);
          });

          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            expect.arrayContaining(expectedTempFiles),
            expect.any(String),
            false
          );

          expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledTimes(1);
        });

        it("displays successfully uploaded files as unremovable file cards", async () => {
          claim = new MockClaimBuilder().medicalLeaveReason().create();

          const attachSpy = jest
            .spyOn(appLogic.documents, "attach")
            .mockImplementation(
              jest.fn(() => {
                return [
                  Promise.resolve({ success: true }),
                  Promise.resolve({ success: true }),
                  Promise.resolve({ success: true }),
                ];
              })
            );

          render();

          const tempFiles = [
            makeTempFile({ name: "File1" }),
            makeTempFile({ name: "File2" }),
            makeTempFile({ name: "File3" }),
          ];

          act(() => {
            wrapper.find("FileCardList").simulate("addTempFiles", tempFiles);
          });

          let removableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("file")
            );
          let unremovableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("document")
            );
          expect(removableFileCards).toHaveLength(3);
          expect(unremovableFileCards).toHaveLength(0);

          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          const newDocuments = [
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
          ];

          wrapper.setProps({ documents: newDocuments }); // force the documents to update because we don't have access to the collection in useDocumentsLogic

          removableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("file")
            );
          unremovableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("document")
            );
          expect(removableFileCards).toHaveLength(0);
          expect(unremovableFileCards).toHaveLength(3);

          attachSpy.mockRestore();
        });

        it("displays unsucessfully uploaded files as removable file cards", async () => {
          claim = new MockClaimBuilder().medicalLeaveReason().create();

          const attachSpy = jest
            .spyOn(appLogic.documents, "attach")
            .mockImplementation(
              jest.fn(() => {
                return [
                  Promise.resolve({ success: true }),
                  Promise.resolve({ success: true }),
                  Promise.resolve({ success: false }),
                ];
              })
            );

          render();

          const tempFiles = [
            makeTempFile({ name: "File1" }),
            makeTempFile({ name: "File2" }),
            makeTempFile({ name: "File3" }),
          ];

          act(() => {
            wrapper.find("FileCardList").simulate("addTempFiles", tempFiles);
          });

          let removableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("file")
            );
          let unremovableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("document")
            );
          expect(removableFileCards).toHaveLength(3);
          expect(unremovableFileCards).toHaveLength(0);

          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          const newDocuments = [
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
          ];

          wrapper.setProps({ documents: newDocuments }); // force the documents to update because we don't have access to the collection in useDocumentsLogic

          removableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("file")
            );
          unremovableFileCards = wrapper
            .find("FileCardList")
            .dive()
            .findWhere(
              (component) =>
                component.name() === "FileCard" && component.prop("document")
            );
          expect(removableFileCards).toHaveLength(1);
          expect(unremovableFileCards).toHaveLength(2);
          expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();

          attachSpy.mockRestore();
        });
      });

      describe("when there are previously loaded documents", () => {
        it("renders the FileCardList with documents", async () => {
          const newDoc = new Document({
            document_type: DocumentType.medicalCertification,
            application_id: claim.application_id,
            fineos_document_id: "testId",
          });
          appLogic.documents.documents = await appLogic.documents.documents.addItem(
            newDoc
          );
          render();
          expect(wrapper.find("FileCardList").props().documents).toHaveLength(
            1
          );
        });

        it("makes API request when there are new files", async () => {
          claim = new MockClaimBuilder().create();
          appLogic.documents.documents = appLogic.documents.documents.addItem(
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: "testId",
            })
          );
          render();

          // Add files to the page state
          const tempFiles = [
            makeTempFile({ name: "file1" }),
            makeTempFile({ name: "file2" }),
          ];

          act(() => {
            wrapper.find("FileCardList").simulate("addTempFiles", tempFiles);
          });

          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            expect.arrayContaining(expectedTempFiles),
            expect.any(String),
            false
          );
        });

        it("skips an API request if there are no new files added", async () => {
          appLogic.documents.documents = appLogic.documents.documents.addItem(
            new Document({
              document_type: DocumentType.medicalCertification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: "testId",
            })
          );

          render();

          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.documents.attach).not.toHaveBeenCalled();
          expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledTimes(1);
        });
      });
    });

    describe("when leave reason is Bonding leave", () => {
      it("renders page with bonding leave content", () => {
        claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
        appLogic.claims.claims = new ClaimCollection([claim]);
        render();
        // Only take snapshots of the i18n content
        expect(wrapper.find("Heading")).toMatchSnapshot();
        expect(wrapper.find("Trans").dive()).toMatchSnapshot();
      });
    });
  });

  describe("there is an error while loading document", () => {
    it("renders alert", () => {
      ({ wrapper } = renderWithAppLogic(UploadCertification, {
        claimAttrs: claim,
        diveLevels,
        hasLoadingDocumentsError: true,
      }));
      expect(wrapper.exists("Alert")).toBe(true);
    });
  });

  it("When uploading additional docs", async () => {
    ({ appLogic, wrapper } = renderWithAppLogic(UploadCertification, {
      claimAttrs: new MockClaimBuilder().create(),
      diveLevels,
      props: {
        query: { claim_id: claim.application_id, additionalDoc: "true" },
      },
    }));

    await act(async () => {
      await wrapper.find("QuestionPage").simulate("save");
    });

    expect(appLogic.documents.attach).toHaveBeenCalledWith(
      claim.application_id,
      [],
      "State managed Paid Leave Confirmation",
      true
    );
  });
});
