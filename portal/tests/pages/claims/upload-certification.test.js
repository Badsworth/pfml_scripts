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
      });

      describe("when the form is successfully submitted", () => {
        it("calls claimsLogic.documents.attach", async () => {
          render();
          const files = [makeFile(), makeFile(), makeFile()];
          const formattedFiles = files.map((file) => {
            return { id: expect.any(String), file };
          });
          const event = {
            target: {
              files,
            },
          };
          const input = wrapper.find("FileCardList").dive().find("input");
          input.simulate("change", event);
          await act(async () => {
            await wrapper.find("QuestionPage").simulate("save");
          });

          expect(appLogic.documents.attach).toHaveBeenCalledWith(
            claim.application_id,
            formattedFiles,
            expect.any(String)
          );
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
});
