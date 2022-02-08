// babel.config.js
module.exports = {
  plugins: ["@babel/plugin-proposal-class-properties"],
  presets: [
    [
      "@babel/preset-env",
      {
        bugfixes: true,
        targets: {
          node: "14",
        },
      },
    ],
    "@babel/preset-typescript",
  ],
};
