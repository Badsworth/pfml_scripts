import { Employer } from "../dor";

const employerPool = [
  {
    accountKey: "12345678910",
    name: "Wayne Enterprises",
    fein: "84-7847847",
    street: "1 Wayne Tower",
    city: "Gotham City",
    state: "MA",
    zip: "01010-1234",
    dba: "",
    family_exemption: false,
    medical_exemption: false,
    updated_date: new Date(),
  },
  {
    accountKey: "12345678911",
    name: "Umbrella Corp",
    fein: "99-9999999",
    street: "545 S Birdneck RD STE 202B",
    city: "Racoon City",
    state: "MA",
    zip: "01010-1234",
    dba: "",
    family_exemption: false,
    medical_exemption: false,
    updated_date: new Date(),
  },
] as Employer[];

export default employerPool;
