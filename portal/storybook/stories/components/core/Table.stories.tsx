import { Props } from "types/common";
import React from "react";
import Table from "src/components/core/Table";

export default {
  title: "Core Components/Table",
  component: Table,
};

export const Default = (args: Props<typeof Table>) => {
  const headings = ["Date range", "Benefit type", "Amount"];

  return (
    <Table {...args}>
      <caption>Employer benefits</caption>
      <thead>
        <tr>
          {headings.map((heading) => (
            <th scope="col" key={heading}>
              {heading}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        <tr>
          <th data-label={headings[0]} scope="row">
            1/1/2020 – 2/1/2020
          </th>
          <td data-label={headings[1]}>Short-term disability insurance</td>
          <td data-label={headings[2]}>$1,000</td>
        </tr>
        <tr>
          <th data-label={headings[0]} scope="row">
            2/1/2020 - 3/1/2020
          </th>
          <td data-label={headings[1]}>Permanent disability insurance</td>
          <td data-label={headings[2]}>$2,000</td>
        </tr>
      </tbody>
    </Table>
  );
};

export const Responsive = () => {
  const headings = ["Employee name", "Organization", "Application ID"];

  return (
    <Table className="width-full" responsive>
      <thead>
        <tr>
          {headings.map((heading) => (
            <th scope="col" key={heading}>
              {heading}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        <tr>
          <th data-label={headings[0]} scope="row">
            Bud Baxter
          </th>
          <td data-label={headings[1]}>Acme Co.</td>
          <td data-label={headings[2]}>NTN-101-ABS-01</td>
        </tr>
        <tr>
          <th data-label={headings[0]} scope="row">
            Ronald McDonald
          </th>
          <td data-label={headings[1]}>Heinz</td>
          <td data-label={headings[2]}>NTN-101-ABS-02</td>
        </tr>
        <tr>
          <th data-label={headings[0]} scope="row">
            Joe Schmoe
          </th>
          <td data-label={headings[1]}>Acme Co.</td>
          <td data-label={headings[2]}>NTN-101-ABS-03</td>
        </tr>
      </tbody>
    </Table>
  );
};
