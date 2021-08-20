/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

// move to '/types' folder
type Address =  {
  city: string | null,
  line_1: string | null,
  line_2: string | null,
  state: string | null,
  zip: string | null,
}

class AddressModel extends BaseModel<Address> {
  defaults() {
      return {
          city: null,
          line_1: null,
          line_2: null,
          state: null,
          zip: null,
      };
  }
}

export default AddressModel;

// const testAddress = new AddressModel({
//   city: "sf",
//   line_1: "44 aaa",
//   line_2: null,
//   state: "ca",
//   zip: "94117",

// });
// const emptyAddress = new AddressModel()
// console.log(",,,,,", testAddress,emptyAddress);