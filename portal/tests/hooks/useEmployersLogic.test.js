import { BadRequestError, ForbiddenError } from "../../src/errors";
import { act, renderHook } from "@testing-library/react-hooks";
import {
  addEmployerMock,
  downloadDocumentMock,
  getClaimMock,
  getDocumentsMock,
  getWithholdingMock,
  submitClaimReviewMock,
  submitWithholdingMock,
} from "../../src/api/EmployersApi";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import User from "../../src/models/User";
import tracker from "../../src/services/tracker";
import { uniqueId } from "lodash";
import useEmployersLogic from "../../src/hooks/useEmployersLogic";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/EmployersApi");
jest.mock("../../src/services/tracker");

describe("useEmployersLogic", () => {
  const absenceId = "mock-fineos-absence-id-1";
  const employerId = "mock-employer-id";
  let clearClaims, employersLogic, errorsLogic, portalFlow, setUser;

  function setup() {
    clearClaims = jest.fn();
    setUser = jest.fn();
    renderHook(() => {
      portalFlow = usePortalFlow();
      errorsLogic = useErrorsLogic({ portalFlow });
      employersLogic = useEmployersLogic({
        errorsLogic,
        clearClaims,
        portalFlow,
        setUser,
      });
    });
  }

  beforeEach(() => {
    setup();
  });

  afterEach(() => {
    errorsLogic = null;
    employersLogic = null;
    portalFlow = null;
    setUser = null;
  });

  describe("addEmployer", () => {
    const postData = {
      ein: "123456789",
    };

    it("makes API call with POST data", async () => {
      await act(async () => {
        await employersLogic.addEmployer(postData);
      });

      expect(addEmployerMock).toHaveBeenCalledWith(postData);
    });

    it("clears the current user", async () => {
      await act(async () => {
        await employersLogic.addEmployer(postData);
      });

      expect(setUser).toHaveBeenCalledWith(undefined);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        addEmployerMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.addEmployer({ ein: "" });
        });

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new Error()]);
        });

        await act(async () => {
          await employersLogic.addEmployer(postData);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });
    });
  });

  describe("loadClaim", () => {
    it("returns loadClaim as instance of function", () => {
      expect(employersLogic.loadClaim).toBeInstanceOf(Function);
    });

    it("makes call to retrieve claim", async () => {
      const secondClaimAbsenceId = "mock-fineos-absence-id-2";

      await act(async () => {
        await employersLogic.loadClaim(absenceId);
      });

      expect(getClaimMock).toHaveBeenCalledWith(absenceId);

      await act(async () => {
        await employersLogic.loadClaim(secondClaimAbsenceId);
      });

      expect(getClaimMock).toHaveBeenCalledWith(secondClaimAbsenceId);
      expect(getClaimMock).toHaveBeenCalledTimes(2);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches generic errors", async () => {
        getClaimMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.loadClaim(absenceId);
        });

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });

      it("redirects to verify contributions page when request fails and includes truthy has_verification_data response field", async () => {
        const goToSpy = jest.spyOn(portalFlow, "goTo");
        getClaimMock.mockImplementationOnce(() => {
          throw new ForbiddenError(
            {
              employer_id: "some-employer-id",
              has_verification_data: true,
            },
            "User is not Verified"
          );
        });

        await act(async () => {
          await employersLogic.loadClaim(absenceId);
        });

        expect(goToSpy).toHaveBeenCalledWith(
          "/employers/organizations/verify-contributions",
          {
            employer_id: "some-employer-id",
            next: "",
          },
          { redirect: true }
        );
        expect(tracker.trackEvent).toHaveBeenCalledWith(
          "LeaveAdminForbiddenError",
          {
            employerId: "some-employer-id",
            hasVerificationData: "true",
          }
        );
      });

      it("redirects to cannot verify page when request fails and includes falsey has_verification_data response field", async () => {
        const goToSpy = jest.spyOn(portalFlow, "goTo");
        getClaimMock.mockImplementationOnce(() => {
          throw new ForbiddenError(
            {
              employer_id: "some-employer-id",
              has_verification_data: false,
            },
            "User is not Verified"
          );
        });

        await act(async () => {
          await employersLogic.loadClaim(absenceId);
        });

        expect(goToSpy).toHaveBeenCalledWith(
          "/employers/organizations/cannot-verify",
          {
            employer_id: "some-employer-id",
          },
          { redirect: true }
        );
        expect(tracker.trackEvent).toHaveBeenCalledWith(
          "LeaveAdminForbiddenError",
          {
            employerId: "some-employer-id",
            hasVerificationData: "false",
          }
        );
      });
    });

    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new Error()]);
      });

      await act(async () => {
        await employersLogic.loadClaim(absenceId);
      });

      expect(errorsLogic.errors).toHaveLength(0);
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

    describe("when the API returns documents", () => {
      const denialNotice = {
        name: "Denial notice",
        fineos_document_id: "67899",
      };
      const approvalNotice = {
        name: "Approval notice",
        fineos_document_id: "78789",
      };

      it("fetches all documents for an application and adds to the claimDocumentsMap", async () => {
        const absenceId = "NTN-323-ABS-01";
        const expectedDocumentsMap = new Map([
          [
            absenceId,
            new ApiResourceCollection("fineos_document_id", [approvalNotice]),
          ],
        ]);
        let { claimDocumentsMap } = employersLogic;

        getDocumentsMock.mockImplementationOnce(() => {
          return {
            success: true,
            status: 200,
            documents: new ApiResourceCollection("fineos_document_id", [
              approvalNotice,
            ]),
          };
        });

        await act(async () => {
          await employersLogic.loadDocuments(absenceId);
        });
        ({ claimDocumentsMap } = employersLogic);
        expect(claimDocumentsMap).toEqual(expectedDocumentsMap);
      });

      it("fetches documents for two absence cases and saves them to the claimDocumentsMap", async () => {
        const absenceCaseId_first = "NTN-323-ABS-01";
        const absenceCaseId_second = "NTN-423-ABS-01";
        const expectedDocumentsMap = new Map([
          [
            absenceCaseId_first,
            new ApiResourceCollection("fineos_document_id", [approvalNotice]),
          ],
          [
            absenceCaseId_second,
            new ApiResourceCollection("fineos_document_id", [denialNotice]),
          ],
        ]);
        let { claimDocumentsMap } = employersLogic;

        getDocumentsMock
          .mockImplementationOnce(() => {
            return {
              success: true,
              status: 200,
              documents: new ApiResourceCollection("fineos_document_id", [
                approvalNotice,
              ]),
            };
          })
          .mockImplementationOnce(() => {
            return {
              success: true,
              status: 200,
              documents: new ApiResourceCollection("fineos_document_id", [
                denialNotice,
              ]),
            };
          });

        await act(async () => {
          await employersLogic.loadDocuments(absenceCaseId_first);
          await employersLogic.loadDocuments(absenceCaseId_second);
        });

        ({ claimDocumentsMap } = employersLogic);
        expect(claimDocumentsMap).toEqual(expectedDocumentsMap);
      });

      it("fetches documents for the same absence case twice and only calls the API once", async () => {
        const absenceId = "NTN-323-ABS-01";
        const expectedDocumentsMap = new Map([
          [
            absenceId,
            new ApiResourceCollection("fineos_document_id", [approvalNotice]),
          ],
        ]);
        let { claimDocumentsMap } = employersLogic;

        getDocumentsMock.mockImplementationOnce(() => {
          return {
            success: true,
            status: 200,
            documents: new ApiResourceCollection("fineos_document_id", [
              approvalNotice,
            ]),
          };
        });

        await act(async () => {
          await employersLogic.loadDocuments(absenceId);
          await employersLogic.loadDocuments(absenceId);
        });

        ({ claimDocumentsMap } = employersLogic);
        expect(getDocumentsMock).toHaveBeenCalledTimes(1);
        expect(claimDocumentsMap).toEqual(expectedDocumentsMap);
      });
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

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new Error()]);
        });

        await act(async () => {
          await employersLogic.loadDocuments(absenceId);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });
    });
  });

  describe("loadWithholding", () => {
    it("renders loadWithholding as instance of function", () => {
      expect(employersLogic.loadWithholding).toBeInstanceOf(Function);
    });

    it("makes a call to retrive withholding data", async () => {
      await act(async () => {
        await employersLogic.loadWithholding(employerId);
      });

      expect(getWithholdingMock).toHaveBeenCalledWith(employerId);
    });

    describe("errors", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches error", async () => {
        getWithholdingMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await employersLogic.loadWithholding(employerId);
        });

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });
    });
  });

  describe("downloadDocument", () => {
    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new Error()]);
      });

      const document = new Document({
        absence_id: "some-absence-id",
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      await act(async () => {
        await employersLogic.downloadDocument(absenceId, document);
      });

      expect(errorsLogic.errors).toHaveLength(0);
    });

    it("makes a request to the API", () => {
      const document = new Document({
        absence_id: "some-absence-id",
        content_type: "image/png",
        fineos_document_id: uniqueId(),
      });

      act(() => {
        employersLogic.downloadDocument(document, absenceId);
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

      expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
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

    it("clears the cached EmployerClaim and claims", async () => {
      await act(async () => {
        await employersLogic.loadClaim(absenceId);
        await employersLogic.submitClaimReview(absenceId, patchData);
      });

      expect(employersLogic.claim).toBeNull();
      expect(clearClaims).toHaveBeenCalled();
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

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new Error()]);
        });

        await act(async () => {
          await employersLogic.submitClaimReview(absenceId, patchData);
        });

        expect(errorsLogic.errors).toHaveLength(0);
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

    it("updates the user", async () => {
      await act(async () => {
        await employersLogic.submitWithholding(postData);
      });

      expect(setUser).toHaveBeenCalledWith(expect.any(User));
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

        expect(errorsLogic.errors[0].name).toEqual("Error");
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new Error()]);
        });

        await act(async () => {
          await employersLogic.submitWithholding(postData);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });
    });
  });
});
