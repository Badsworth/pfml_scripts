/**
 * Intercept HTTP requests and return a mocked response. Only mocks the first fetch request,
 * using mockResolvedValueOnce!
 * @param {object} [mockData]
 * @param {object} [mockData.response]
 * @param {number} [mockData.status]
 */
const mockFetch = ({ response = { data: [] }, status = 200 } = {}) => {
  global.fetch = jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok: status < 300,
    status,
  });
};

export default mockFetch;
