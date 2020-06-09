import BaseModel from "./BaseModel";

class User extends BaseModel {
  get defaults() {
    return {
      user_id: null,
      auth_id: null,
      email_address: null,
      date_of_birth: null,
      has_state_id: null,
      state_id: null,
      status: null,
      ssn_or_itin: null,
    };
  }
}

export default User;
