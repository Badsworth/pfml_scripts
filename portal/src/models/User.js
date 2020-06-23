/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

class User extends BaseModel {
  get defaults() {
    return {
      auth_id: null,
      consented_to_data_sharing: null,
      date_of_birth: null,
      email_address: null,
      has_state_id: null,
      state_id: null,
      status: null,
      user_id: null,
    };
  }
}

export default User;
