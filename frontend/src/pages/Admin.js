import { useEffect, useState } from "react";
import client from "../api/client";

export default function AdminDashboard() {
  const [impact, setImpact] = useState({});

  useEffect(() => {
    async function fetchImpact() {
      const res = await client.get("/dashboard/impact");
      setImpact(res.data);
    }
    fetchImpact();
  }, []);

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <p>Total Donations: {impact.total_donations}</p>
      <p>Completed: {impact.completed_donations}</p>
      <p>Expired: {impact.expired_donations}</p>
      <p>Completion Rate: {impact.completion_rate}%</p>
    </div>
  );
}
