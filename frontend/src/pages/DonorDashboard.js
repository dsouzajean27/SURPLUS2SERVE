import { useEffect, useState } from "react";
import client from "../api/client";

export default function DonorDashboard() {
  const [donations, setDonations] = useState([]);

  useEffect(() => {
    async function fetchDonations() {
      const res = await client.get("/donations");
      setDonations(res.data);
    }
    fetchDonations();
  }, []);

  return (
    <div>
      <h2>Your Donations</h2>
      <ul>
        {donations.map((d) => (
          <li key={d.id}>{d.food_type} - {d.quantity} units</li>
        ))}
      </ul>
    </div>
  );
}
