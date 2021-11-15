const buildEnv = process.env.BUILD_ENV || "development";

module.exports = {
  reactStrictMode: true,
  images: {
    domains: ["via.placeholder.com"],
  },
};
