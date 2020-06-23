import User from "../../src/models/User";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let claims,
      createClaim,
      loadClaims,
      login,
      requireUserConsentToDataAgreement,
      rest,
      submitClaim,
      updateClaim;
    const user = new User();

    testHook(() => {
      ({
        claims,
        createClaim,
        loadClaims,
        login,
        requireUserConsentToDataAgreement,
        submitClaim,
        updateClaim,
        ...rest
      } = useAppLogic({ user }));
    });

    expect(claims).toBeNull();
    expect(loadClaims).toBeInstanceOf(Function);
    expect(login).toBeInstanceOf(Function);
    expect(createClaim).toBeInstanceOf(Function);
    expect(updateClaim).toBeInstanceOf(Function);
    expect(requireUserConsentToDataAgreement).toBeInstanceOf(Function);
    expect(submitClaim).toBeInstanceOf(Function);
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
