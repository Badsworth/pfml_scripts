import BaseModel from "./BaseModel";

class User extends BaseModel {
  get defaults() {
    return {
      user_id: null,
      auth_id: null,
      email_address: null,
      first_name: null,
      middle_name: null,
      last_name: null,
      date_of_birth: null,
      has_state_id: null,
      state_id: null,
      status: null,
      ssn_or_itin: null,
    };
  }
}

export default User;
