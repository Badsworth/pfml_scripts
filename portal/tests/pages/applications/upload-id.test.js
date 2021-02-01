/* eslint-disable lodash/import-scope */
import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import _, { uniqueId } from "lodash";
import ClaimCollection from "../../../src/models/ClaimCollection";
import UploadId from "../../../src/pages/applications/upload-id";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");
jest.mock("../../../src/services/tracker");

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

describe("UploadId", () => {
  let appLogic, claim, wrapper;

  describe("before any documents have been loaded", () => {
    function render() {
      ({ appLogic, wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: claim,
        diveLevels,
      }));
    }
    beforeEach(() => {
      render();
    });

    it("does not render a FileCardList", () => {
      expect(wrapper.find("FileCardList")).toEqual({});
    });

    it("renders a spinner", () => {
      expect(wrapper.find("Spinner")).toHaveLength(1);
      expect(wrapper.find("Spinner")).toMatchSnapshot();
    });

    it("does not render the ReviewRow block", () => {
      expect(wrapper.find("ReviewRow")).toEqual({});
    });
  });

  describe("after documents have been loaded", () => {
    function render() {
      ({ wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: claim,
        diveLevels,
        props: { appLogic },
      }));
    }

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

    describe("when the user doesn't have a Mass ID", () => {
      it("renders the page with 'Other' ID content", () => {
        claim = new MockClaimBuilder().medicalLeaveReason().create();
        claim.has_state_id = false;
        appLogic.claims.claims = new ClaimCollection([claim]);
        render();
        expect(wrapper).toMatchSnapshot();
      });
    });

    describe("when the user has a Mass ID", () => {
      const filesWithUniqueId = [
        { id: "1", file: makeFile({ name: "file1" }) },
        { id: "2", file: makeFile({ name: "file2" }) },
      ];
      beforeEach(() => {
        claim = new MockClaimBuilder().medicalLeaveReason().create();
        claim.has_state_id = true;
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

      it("renders the page with Mass ID content", () => {
        render();
        expect(wrapper).toMatchSnapshot();
      });

      describe("when the user uploads files", () => {
        it("renders filecards for the files", () => {
          render();
          const files = [makeFile(), makeFile(), makeFile()];
          const event = {
            target: {
              files,
            },
          };

          const input = wrapper.find("FileCardList").dive().find("input");
          act(() => {
            input.simulate("change", event);
          });

          expect(wrapper).toMatchSnapshot();
        });

        it("makes documents.attach request when no documents exist", async () => {
          let id = 0;
          jest.spyOn(_, "uniqueId").mockImplementation(() => String(++id));
          claim = new MockClaimBuilder().create();
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

          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            filesWithUniqueId,
            expect.any(String),
            false
          );
        });

        it("navigates the user to the next page if there are no errors", async () => {
          render();
          const files = [makeFile(), makeFile(), makeFile()];
          const event = {
            target: {
              files,
            },
          };

          const input = wrapper.find("FileCardList").dive().find("input");
          await act(async () => {
            input.simulate("change", event);
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalled();
        });

        it("does not navigate the user to the next page if there are errors", async () => {
          jest
            .spyOn(appLogic.documents, "attach")
            .mockImplementationOnce(() => [
              Promise.resolve({ success: false }),
            ]);
          render();
          const files = [makeFile()];
          const event = {
            target: {
              files,
            },
          };

          const input = wrapper.find("FileCardList").dive().find("input");
          await act(async () => {
            input.simulate("change", event);
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
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

          const files = [
            makeFile({ name: "File1" }),
            makeFile({ name: "File2" }),
            makeFile({ name: "File3" }),
          ];
          const event = {
            target: {
              files,
            },
          };

          const input = wrapper.find("FileCardList").dive().find("input");
          act(() => {
            input.simulate("change", event);
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
              document_type: DocumentType.identityVerification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.identityVerification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.identityVerification,
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

          const files = [
            makeFile({ name: "File1" }),
            makeFile({ name: "File2" }),
            makeFile({ name: "File3" }),
          ];
          const event = {
            target: {
              files,
            },
          };

          const input = wrapper.find("FileCardList").dive().find("input");
          act(() => {
            input.simulate("change", event);
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
              document_type: DocumentType.identityVerification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: uniqueId(),
            }),
            new Document({
              document_type: DocumentType.identityVerification,
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

          attachSpy.mockRestore();
        });
      });

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

      describe("when there are previously loaded documents", () => {
        it("renders the FileCardList with documents", async () => {
          const newDoc = new Document({
            document_type: DocumentType.identityVerification,
            application_id: claim.application_id,
            created_at: "2020-10-12",
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
          let id = 0;
          jest.spyOn(_, "uniqueId").mockImplementation(() => String(++id));
          claim = new MockClaimBuilder().create();
          appLogic.documents.documents = appLogic.documents.documents.addItem(
            new Document({
              document_type: DocumentType.identityVerification,
              application_id: claim.application_id,
              created_at: "2020-10-12",
              fineos_document_id: "testId",
            })
          );
          render();

          // Add files to the page state
          const files = [makeFile(), makeFile()];
          const input = wrapper.find("FileCardList").dive().find("input");
          await act(async () => {
            input.simulate("change", {
              target: {
                files,
              },
            });
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            filesWithUniqueId,
            expect.any(String),
            false
          );
        });

        it("skips an API request if there are no new files added", async () => {
          appLogic.documents.documents = appLogic.documents.documents.addItem(
            new Document({
              document_type: DocumentType.identityVerification,
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
  });

  describe("there is an error while loading document", () => {
    it("renders alert", () => {
      ({ wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: claim,
        diveLevels,
        hasLoadingDocumentsError: true,
      }));
      expect(wrapper.exists("Alert")).toBe(true);
    });
  });

  it("When uploading additional docs", async () => {
    ({ appLogic, wrapper } = renderWithAppLogic(UploadId, {
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
      "Identification Proof",
      true
    );
  });
});
