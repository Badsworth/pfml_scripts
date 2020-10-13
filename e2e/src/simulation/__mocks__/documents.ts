import { jest } from "@jest/globals";

export default {
  HCP: jest.fn(() => Promise.resolve()),
  MASSID: jest.fn(() => Promise.resolve()),
  OOSID: jest.fn(() => Promise.resolve()),
};
