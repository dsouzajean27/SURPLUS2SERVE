import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Impact from "./pages/Impact";
import DonorDashboard from "./pages/DonorDashboard";
import PostDonation from "./pages/PostDonation";
import DonationDetail from "./pages/DonationDetail";
import NGODashboard from "./pages/NGODashboard";
import AvailableDonations from "./pages/AvailableDonations";
import Pickups from "./pages/Pickups";
import Requirements from "./pages/Requirements";
import Demand from "./pages/Demand";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import AdminDashboard from "./pages/Admin";
import { homePathFor } from "./utils";

function Protected({ roles, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homePathFor(user.role)} replace />;
  return children;
}

function Home() {
  const { user } = useAuth();
  return <Navigate to={user ? homePathFor(user.role) : "/login"} replace />;
}

function ImpactRoute() {
  const { user } = useAuth();
  return user ? <Layout><Impact /></Layout> : <Impact />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login mode="login" />} />
          <Route path="/register" element={<Login mode="register" />} />
          <Route path="/" element={<Home />} />
          <Route path="/impact" element={<ImpactRoute />} />
          <Route element={<Protected><Layout /></Protected>}>
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/donations/:id" element={<DonationDetail />} />
            <Route path="/donor" element={<Protected roles={["donor"]}><DonorDashboard /></Protected>} />
            <Route path="/donor/new" element={<Protected roles={["donor"]}><PostDonation /></Protected>} />
            <Route path="/ngo" element={<Protected roles={["ngo"]}><NGODashboard /></Protected>} />
            <Route path="/ngo/donations" element={<Protected roles={["ngo"]}><AvailableDonations /></Protected>} />
            <Route path="/ngo/pickups" element={<Protected roles={["ngo"]}><Pickups /></Protected>} />
            <Route path="/ngo/requirements" element={<Protected roles={["ngo"]}><Requirements /></Protected>} />
            <Route path="/demand" element={<Protected roles={["ngo", "admin"]}><Demand /></Protected>} />
            <Route path="/admin" element={<Protected roles={["admin"]}><AdminDashboard /></Protected>} />
          </Route>
          <Route path="*" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
