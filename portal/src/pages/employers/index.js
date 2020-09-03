import Link from "next/link";
import React from "react";
import routes from "../../routes";

export const Index = () => {
  return (
    <div>
      <Link href={routes.employers.review}>Review claim</Link>
    </div>
  );
};

export default Index;
