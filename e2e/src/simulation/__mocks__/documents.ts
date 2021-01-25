import { jest } from "@jest/globals";

export default {
  HCP: jest.fn(() => Promise.resolve(Buffer.alloc(1))),
  MASSID: jest.fn(() => Promise.resolve(Buffer.alloc(1))),
  OOSID: jest.fn(() => Promise.resolve(Buffer.alloc(1))),
};
