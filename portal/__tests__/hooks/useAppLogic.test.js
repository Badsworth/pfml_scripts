import User from "../../src/models/User";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let appErrors,
      auth,
      claims,
      clearErrors,
      createClaim,
      loadClaims,
      rest,
      setAppErrors,
      submitClaim,
      updateClaim;
    const user = new User();

    testHook(() => {
      ({
        appErrors,
        auth,
        claims,
        clearErrors,
        createClaim,
        loadClaims,
        setAppErrors,
        submitClaim,
        updateClaim,
        ...rest
      } = useAppLogic({ user }));
    });

    expect(appErrors).toBeNull();
    expect(auth).toEqual(expect.anything());
    expect(claims).toBeNull();
    expect(clearErrors).toBeInstanceOf(Function);
    expect(loadClaims).toBeInstanceOf(Function);
    expect(createClaim).toBeInstanceOf(Function);
    expect(updateClaim).toBeInstanceOf(Function);
    expect(setAppErrors).toBeInstanceOf(Function);
    expect(submitClaim).toBeInstanceOf(Function);
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
