import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("useAppLogic", () => {
  it("returns app state and getter and setter methods", () => {
    let appErrors,
      auth,
      claims,
      clearErrors,
      goToNextPage,
      rest,
      setAppErrors,
      users;

    testHook(() => {
      ({
        appErrors,
        auth,
        claims,
        clearErrors,
        goToNextPage,
        setAppErrors,
        users,
        ...rest
      } = useAppLogic());
    });

    expect(appErrors).toBeInstanceOf(AppErrorInfoCollection);
    expect(appErrors.items).toHaveLength(0);
    expect(auth).toEqual(expect.anything());
    expect(claims.claims).toBeNull();
    expect(clearErrors).toBeInstanceOf(Function);
    expect(goToNextPage).toBeInstanceOf(Function);
    expect(claims.load).toBeInstanceOf(Function);
    expect(claims.create).toBeInstanceOf(Function);
    expect(claims.update).toBeInstanceOf(Function);
    expect(users.updateUser).toBeInstanceOf(Function);
    expect(setAppErrors).toBeInstanceOf(Function);
    expect(claims.submit).toBeInstanceOf(Function);
    expect(users.user).toBeUndefined();
    expect(users).toEqual(expect.anything());
    // there should be no other properties;
    expect(rest).toEqual({});
  });
});
