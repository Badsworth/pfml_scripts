/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class User extends BaseModel {
  get defaults() {
    return {
      auth_id: null,
      consented_to_data_sharing: null,
      email_address: null,
      status: null,
      user_id: null,
    };
  }
}

export default User;
