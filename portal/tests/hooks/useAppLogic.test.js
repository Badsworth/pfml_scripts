import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import ClaimCollection from "../../src/models/ClaimCollection";
import DocumentCollection from "../../src/models/DocumentCollection";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let _appErrorsLogic,
      appErrors,
      auth,
      benefitsApplications,
      catchError,
      claims,
      clearErrors,
      documents,
      employers,
      otherLeaves,
      portalFlow,
      rest,
      setAppErrors,
      users;

    testHook(() => {
      ({
        appErrors,
        _appErrorsLogic,
        auth,
        catchError,
        claims,
        benefitsApplications,
        documents,
        employers,
        clearErrors,
        portalFlow,
        otherLeaves,
        setAppErrors,
        users,
        ...rest
      } = useAppLogic());
    });

    expect(appErrors).toBeInstanceOf(AppErrorInfoCollection);
    expect(appErrors.items).toHaveLength(0);
    expect(_appErrorsLogic).toEqual(expect.anything());
    expect(auth).toEqual(expect.anything());
    expect(catchError).toBeInstanceOf(Function);
    expect(benefitsApplications.benefitsApplications).toBeInstanceOf(
      BenefitsApplicationCollection
    );
    expect(clearErrors).toBeInstanceOf(Function);
    expect(portalFlow).toEqual(expect.anything());
    expect(benefitsApplications.hasLoadedAll).toEqual(expect.any(Boolean));
    expect(benefitsApplications.load).toBeInstanceOf(Function);
    expect(benefitsApplications.loadAll).toBeInstanceOf(Function);
    expect(benefitsApplications.create).toBeInstanceOf(Function);
    expect(benefitsApplications.update).toBeInstanceOf(Function);
    expect(claims.claims).toBeInstanceOf(ClaimCollection);
    expect(claims.hasLoadedAll).toEqual(expect.any(Boolean));
    expect(claims.loadAll).toBeInstanceOf(Function);
    expect(users.updateUser).toBeInstanceOf(Function);
    expect(setAppErrors).toBeInstanceOf(Function);
    expect(benefitsApplications.submit).toBeInstanceOf(Function);
    expect(documents.documents).toBeInstanceOf(DocumentCollection);
    expect(documents.loadAll).toBeInstanceOf(Function);
    expect(documents.attach).toBeInstanceOf(Function);
    expect(employers.loadWithholding).toBeInstanceOf(Function);
    expect(employers.submitClaimReview).toBeInstanceOf(Function);
    expect(employers.submitWithholding).toBeInstanceOf(Function);
    expect(otherLeaves.removeEmployerBenefit).toBeInstanceOf(Function);
    expect(otherLeaves.removeOtherIncome).toBeInstanceOf(Function);
    expect(otherLeaves.removePreviousLeave).toBeInstanceOf(Function);
    expect(users.user).toBeUndefined();
    expect(users).toEqual(expect.anything());
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
