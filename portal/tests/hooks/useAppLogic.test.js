import ApiResourceCollection from "src/models/ApiResourceCollection";
import { renderHook } from "@testing-library/react-hooks";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let _errorsLogic,
      auth,
      benefitsApplications,
      catchError,
      claims,
      clearErrors,
      clearRequiredFieldErrors,
      documents,
      employers,
      errors,
      featureFlags,
      payments,
      portalFlow,
      rest,
      setErrors,
      users;

    renderHook(() => {
      ({
        errors,
        _errorsLogic,
        auth,
        benefitsApplications,
        catchError,
        payments,
        claims,
        clearErrors,
        documents,
        employers,
        featureFlags,
        clearRequiredFieldErrors,
        portalFlow,
        setErrors,
        users,
        ...rest
      } = useAppLogic());
    });

    expect(errors).toBeInstanceOf(Array);
    expect(errors).toHaveLength(0);
    expect(_errorsLogic).toEqual(expect.anything());
    expect(auth).toEqual(expect.anything());
    expect(catchError).toBeInstanceOf(Function);
    expect(benefitsApplications.benefitsApplications).toBeInstanceOf(
      ApiResourceCollection
    );
    expect(clearErrors).toBeInstanceOf(Function);
    expect(clearRequiredFieldErrors).toBeInstanceOf(Function);
    expect(portalFlow).toEqual(expect.anything());
    expect(benefitsApplications.load).toBeInstanceOf(Function);
    expect(benefitsApplications.loadPage).toBeInstanceOf(Function);
    expect(benefitsApplications.create).toBeInstanceOf(Function);
    expect(benefitsApplications.update).toBeInstanceOf(Function);
    expect(claims.claims).toBeInstanceOf(ApiResourceCollection);
    expect(claims.loadPage).toBeInstanceOf(Function);
    expect(users.updateUser).toBeInstanceOf(Function);
    expect(setErrors).toBeInstanceOf(Function);
    expect(benefitsApplications.submit).toBeInstanceOf(Function);
    expect(documents.documents).toBeInstanceOf(ApiResourceCollection);
    expect(documents.loadAll).toBeInstanceOf(Function);
    expect(documents.attach).toBeInstanceOf(Function);
    expect(employers.loadWithholding).toBeInstanceOf(Function);
    expect(employers.submitClaimReview).toBeInstanceOf(Function);
    expect(employers.submitWithholding).toBeInstanceOf(Function);
    expect(payments.loadPayments).toBeInstanceOf(Function);
    expect(users.user).toBeUndefined();
    expect(users).toEqual(expect.anything());
    expect(featureFlags).toBeInstanceOf(Object);
    expect(featureFlags.flags).toBeInstanceOf(Array);
    expect(featureFlags.getFlag).toBeInstanceOf(Function);
    expect(featureFlags.loadFlags).toBeInstanceOf(Function);
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
