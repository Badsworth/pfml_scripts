import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import UploadCertification from "../../../src/pages/claims/upload-certification";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadCertification", () => {
  let appLogic, claim, wrapper;

  describe("before any documents have been loaded", () => {
    function render() {
      ({ appLogic, wrapper } = renderWithAppLogic(UploadCertification, {
        claimAttrs: claim,
        diveLevels: 5,
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
        diveLevels: 5,
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

        expect(appLogic.goToNextPage).toHaveBeenCalledWith(
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
        it("passes files to FileCardList", () => {
          render();
          const files = [makeFile(), makeFile(), makeFile()];
          const event = {
            target: {
              files,
            },
          };
          const input = wrapper.find("FileCardList").dive().find("input");
          input.simulate("change", event);

          expect(wrapper.find("FileCardList").prop("files")).toHaveLength(3);
        });

        it("makes API request when no documents exist", async () => {
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

          const expectedFiles = files.map((file) => {
            return { id: expect.any(String), file };
          });
          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            expectedFiles,
            expect.any(String)
          );
        });
      });

      it("makes API request when no documents exist and no new files are added", async () => {
        claim = new MockClaimBuilder().create();

        render();

        await act(async () => {
          await wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.documents.attach).toHaveBeenCalledWith(
          claim.application_id,
          [],
          expect.any(String)
        );
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

          const expectedFiles = files.map((file) => {
            return { id: expect.any(String), file };
          });
          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            expectedFiles,
            expect.any(String)
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
          expect(appLogic.goToNextPage).toHaveBeenCalledTimes(1);
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
        diveLevels: 5,
        hasLoadingDocumentsError: true,
      }));
      expect(wrapper.exists("Alert")).toBe(true);
    });
  });
});
