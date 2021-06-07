// babel.config.js
module.exports = {
  plugins: [
    "@babel/plugin-proposal-class-properties",
  ],
  presets: [
    [
      "@babel/preset-env",
      {
        targets: {
          // Specifically target node 12 for the moment.
          // This works around Cypress using Node 14, while most of us (and CI) are still on Node 12.
          // Can be removed once we bump CI to Node 14.
          node: "12",
        },
      },
    ],
    "@babel/preset-typescript",
  ],
};
