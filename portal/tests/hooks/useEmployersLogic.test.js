import {
  downloadDocumentMock,
  getClaimMock,
  getDocumentsMock,
  submitClaimReviewMock,
  submitWithholdingMock,
} from "../../src/api/EmployersApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { BadRequestError } from "../../src/errors";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import { uniqueId } from "lodash";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useEmployersLogic from "../../src/hooks/useEmployersLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/EmployersApi");
jest.mock("../../src/services/tracker");

describe("useEmployersLogic", () => {
  const absenceId = "mock-fineos-absence-id-1";
  let appErrorsLogic, employersLogic, portalFlow;

  function renderHook() {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
      portalFlow = usePortalFlow();
      employersLogic = useEmployersLogic({ appErrorsLogic, portalFlow });
    });
  }

  beforeEach(() => {
    renderHook();
  });

  afterEach(() => {
    appErrorsLogic = null;
    employersLogic = null;
    portalFlow = null;
  });

  describe("loadClaim", () => {
    it("returns loadClaim as instance of function", () => {
      expect(employersLogic.loadClaim).toBeInstanceOf(Function);
    });

    it("returns claim data", async () => {
      await act(async () => {
        await employersLogic.loadClaim(absenceId);
      });

      expect(getClaimMock).toHaveBeenCalledWith(absenceId);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        getClaimMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.loadClaim(absenceId);
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
        await employersLogic.loadClaim(absenceId);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });
  });

  describe("loadDocuments", () => {
    it("renders loadDocuments as instance of function", () => {
      expect(employersLogic.loadDocuments).toBeInstanceOf(Function);
    });

    it("makes a call to retrieve document data", async () => {
      await act(async () => {
        await employersLogic.loadDocuments(absenceId);
      });

      expect(getDocumentsMock).toHaveBeenCalledWith(absenceId);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        getDocumentsMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.loadDocuments(absenceId);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await employersLogic.loadDocuments(absenceId);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });
  });

  describe("downloadDocument", () => {
    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      const document = new Document({
        absence_id: "some-absence-id",
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      await act(async () => {
        await employersLogic.downloadDocument(absenceId, document);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    it("makes a request to the API", () => {
      const document = new Document({
        absence_id: "some-absence-id",
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      act(() => {
        employersLogic.downloadDocument(absenceId, document);
      });

      expect(downloadDocumentMock).toHaveBeenCalledWith(absenceId, document);
    });

    it("returns a blob", async () => {
      const document = new Document({
        absence_id: "some-absence-id",
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      let response;
      await act(async () => {
        response = await employersLogic.downloadDocument(absenceId, document);
      });

      expect(response).toBeInstanceOf(Blob);
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      downloadDocumentMock.mockImplementationOnce(() => {
        throw new BadRequestError();
      });

      await act(async () => {
        await employersLogic.downloadDocument();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toEqual("BadRequestError");
    });
  });

  describe("submitClaimReview", () => {
    const patchData = {
      employer_notification_date: "01-01-2021",
      employer_benefits: [],
      previous_leaves: [],
      hours_worked_per_week: 20,
      comment: "No comment",
    };

    it("returns submit as instance of function", () => {
      expect(employersLogic.submitClaimReview).toBeInstanceOf(Function);
    });

    it("submits with absence id and patch data", async () => {
      await act(async () => {
        await employersLogic.submitClaimReview(absenceId, patchData);
      });

      expect(submitClaimReviewMock).toHaveBeenCalledWith(absenceId, patchData);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        submitClaimReviewMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.submitClaimReview(absenceId, {});
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await employersLogic.submitClaimReview(absenceId, patchData);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });
  });

  describe("submitWithholding", () => {
    const postData = {
      employer_id: "mock_employer_id",
      withholding_amount: "123",
      withholding_quarter: "2020-10-10",
    };

    it("returns submitWithholding as instance of function", () => {
      expect(employersLogic.submitWithholding).toBeInstanceOf(Function);
    });

    it("makes API call with POST data", async () => {
      await act(async () => {
        await employersLogic.submitWithholding(postData);
      });

      expect(submitWithholdingMock).toHaveBeenCalledWith(postData);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        submitWithholdingMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.submitWithholding(absenceId, {});
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await employersLogic.submitWithholding(postData);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });
  });
});
