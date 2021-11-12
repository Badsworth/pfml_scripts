const mockUserSearchResponse = {
  employee_id: "mockUserId",
  tax_identifier_last4: "6789",
  first_name: "mock",
  middle_name: null,
  last_name: "User",
  other_name: null,
  email_address: null,
  phone_number: null,
  organization_units: [
    {
      organization_unit_id: "dep-1",
      fineos_id: "f-dep-1",
      name: "Department One",
      employer_id: "123456789",
      linked: true,
    },
    {
      organization_unit_id: "dep-2",
      fineos_id: "f-dep-2",
      name: "Department Two",
      employer_id: "123456789",
      linked: false,
    },
  ],
};

// Export mocked EmployereApi functions so we can spy on them
export const searchMock = jest.fn().mockResolvedValue(() => {
  return {
    data: mockUserSearchResponse,
    status: 200,
    success: true,
  };
});

const employeesApi = jest.fn().mockImplementation(() => ({
  search: searchMock,
}));

export default employeesApi;
