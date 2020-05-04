import User from "../../src/models/User";
import request from "../../src/api/request";
import usersApi from "../../src/api/usersApi";

jest.mock("../../src/api/request");

describe("users API", () => {
  describe("createUser", () => {
    const user = new User({
      date_of_birth: "02-02-2020",
      first_name: "Fred",
      last_name: "Johnson",
    });

    it("is successful", async () => {
      const response = await usersApi.createUser(user);
      expect(response.success).toBeTruthy();
    });

    it("includes User in the response", async () => {
      const response = await usersApi.createUser(user);

      expect(response.user).toBeInstanceOf(User);
    });

    it("adds user request parameters to the user", async () => {
      const response = await usersApi.createUser(user);

      expect(response.user.date_of_birth).toBe(user.date_of_birth);
      expect(response.user.first_name).toBe(user.first_name);
      expect(response.user.last_name).toBe(user.last_name);
    });

    it("adds status and user_id fields to the user", async () => {
      const response = await usersApi.createUser(user);

      expect(response.user).toMatchObject({
        user_id: expect.any(String),
        status: expect.any(String),
      });
    });
  });

  describe("getCurrentUser", () => {
    describe("when the request succeeds", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
          body: {
            first_name: "Anton",
            last_name: "Mock",
          },
          status: 200,
          success: true,
        });
      });

      it("reports success as true", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.success).toBe(true);
      });

      it("includes User in the response", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.user).toBeInstanceOf(User);
        expect(response.user.first_name).toBe("Anton");
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
          body: {},
          status: 400,
          success: false,
        });
      });

      it("reports success as false", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.success).toBe(false);
      });

      it("does not set the User in the response", async () => {
        expect.assertions();

        const response = await usersApi.getCurrentUser();

        expect(response.user).toBeNull();
      });
    });
  });

  describe("updateUser", () => {
    const user = {
      date_of_birth: "02-02-2020",
      first_name: "Fred",
      last_name: "Johnson",
    };

    it("is successful", async () => {
      const response = await usersApi.updateUser(user);
      expect(response.success).toBeTruthy();
    });

    it("includes User in the response", async () => {
      const response = await usersApi.createUser(user);

      expect(response.user).toBeInstanceOf(User);
    });

    it("adds user request parameters to the user", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toMatchObject(user);
    });

    it("adds status and user_id fields to the user", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toMatchObject({
        user_id: expect.any(String),
        status: expect.any(String),
      });
    });
  });
});
