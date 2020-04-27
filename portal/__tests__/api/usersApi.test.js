import User from "../../src/models/User";
import usersApi from "../../src/api/usersApi";

describe("users API", () => {
  describe("createUser", () => {
    const user = new User({
      dateOfBirth: "02-02-2020",
      firstName: "Fred",
      lastName: "Johnson",
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

      expect(response.user.dateOfBirth).toBe(user.dateOfBirth);
      expect(response.user.firstName).toBe(user.firstName);
      expect(response.user.lastName).toBe(user.lastName);
    });

    it("adds status and userId fields to the user", async () => {
      const response = await usersApi.createUser(user);

      expect(response.user).toMatchObject({
        userId: expect.any(String),
        status: expect.any(String),
      });
    });
  });

  describe("updateUser", () => {
    const user = {
      dateOfBirth: "02-02-2020",
      firstName: "Fred",
      lastName: "Johnson",
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

    it("adds status and userId fields to the user", async () => {
      const response = await usersApi.updateUser(user);

      expect(response.user).toMatchObject({
        userId: expect.any(String),
        status: expect.any(String),
      });
    });
  });
});
