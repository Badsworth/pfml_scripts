import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockClaimBuilder,
  makeFile,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import UploadId from "../../../src/pages/claims/upload-id";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("UploadId", () => {
  let appLogic, claim, wrapper;

  describe("before any documents have been loaded", () => {
    function render() {
      ({ appLogic, wrapper } = renderWithAppLogic(UploadId, {
        claimAttrs: claim,
        diveLevels: 5,
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
    function render(attrs = {}) {
      ({ wrapper } = renderWithAppLogic(UploadId, {
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
      });

      describe("when the form is successfully submitted", () => {
        it("calls claimsLogic.documents.attach", async () => {
          claim = new MockClaimBuilder().create();
          render();
          const files = [makeFile(), makeFile()];
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
        it("renders the ReviewRow component", async () => {
          const newDoc = new Document({
            document_type: DocumentType.identityVerification,
            application_id: claim.application_id,
            fineos_document_id: "testId",
          });
          appLogic.documents.documents = await appLogic.documents.documents.addItem(
            newDoc
          );
          render();
          expect(wrapper.find("ReviewRow")).toMatchSnapshot();
          expect(wrapper.find("ReviewRow")).toHaveLength(1);
        });
      });
    });
  });
});
