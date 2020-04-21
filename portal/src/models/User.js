import BaseModel from "./BaseModel";

class User extends BaseModel {
  get defaults() {
    return {
      userId: null,
      cognitoUserId: null,
      firstName: null,
      middleName: null,
      lastName: null,
      dateOfBirth: null,
      hasStateId: null,
      stateId: null,
      ssn: null,
    };
  }
}

export default User;
