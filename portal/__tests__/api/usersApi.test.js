import User from "../../src/models/User";
import usersApi from "../../src/api/usersApi";

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
