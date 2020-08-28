import { Employer } from "../dor";

const employerPool = [
  {
    accountKey: "00001",
    name: "John Hancock",
    fein: "12-12315",
    street: "123 Some Way",
    city: "Boston",
    state: "MA",
    zip: "01010",
    dba: "",
    family_exemption: false,
    medical_exemption: false,
    updated_date: new Date(),
  },
] as Employer[];

export default employerPool;
