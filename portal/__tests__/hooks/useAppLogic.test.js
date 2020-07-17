import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let appErrors,
      auth,
      claims,
      clearErrors,
      createClaim,
      goToNextPage,
      loadClaims,
      loadUser,
      rest,
      setAppErrors,
      setUser,
      submitClaim,
      updateClaim,
      updateUser,
      user;

    testHook(() => {
      ({
        appErrors,
        auth,
        claims,
        clearErrors,
        createClaim,
        goToNextPage,
        loadClaims,
        loadUser,
        setAppErrors,
        setUser,
        submitClaim,
        updateClaim,
        updateUser,
        user,
        ...rest
      } = useAppLogic());
    });

    expect(appErrors).toBeInstanceOf(AppErrorInfoCollection);
    expect(appErrors.items).toHaveLength(0);
    expect(auth).toEqual(expect.anything());
    expect(claims).toBeNull();
    expect(clearErrors).toBeInstanceOf(Function);
    expect(goToNextPage).toBeInstanceOf(Function);
    expect(loadClaims).toBeInstanceOf(Function);
    expect(loadUser).toBeInstanceOf(Function);
    expect(createClaim).toBeInstanceOf(Function);
    expect(updateClaim).toBeInstanceOf(Function);
    expect(updateUser).toBeInstanceOf(Function);
    expect(setAppErrors).toBeInstanceOf(Function);
    expect(setUser).toBeInstanceOf(Function);
    expect(submitClaim).toBeInstanceOf(Function);
    expect(user).toBeUndefined();
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
