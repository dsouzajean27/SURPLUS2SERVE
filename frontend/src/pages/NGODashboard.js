import { useEffect, useState } from "react";
import client from "../api/client";

export default function NGODashboard({ ngoId }) {
  const [stats, setStats] = useState({});

  useEffect(() => {
    async function fetchStats() {
      const res = await client.get(`/dashboard/ngo/${ngoId}`);
      setStats(res.data);
    }
    fetchStats();
  }, [ngoId]);

  return (
    <div>
      <h2>NGO Dashboard</h2>
      <p>Requirements Posted: {stats.requirements_posted}</p>
      <p>Requirements Fulfilled: {stats.requirements_fulfilled}</p>
    </div>
  );
}
