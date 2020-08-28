import React from "react";
import Table from "src/components/Table";

export default {
  title: "Components/Table",
  component: Table,
};

export const Default = () => {
  return (
    <Table>
      <caption>Employer benefits</caption>
      <thead>
        <tr>
          <th scope="col">Date range</th>
          <th scope="col">Benefit type</th>
          <th scope="col">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">1/1/2020 – 2/1/2020</th>
          <td>Short-term disability insurance</td>
          <td>$1,000</td>
        </tr>
        <tr>
          <th scope="row">2/1/2020-3/1/2020</th>
          <td>Permanent disability insurance</td>
          <td>$2,000</td>
        </tr>
      </tbody>
    </Table>
  );
};
