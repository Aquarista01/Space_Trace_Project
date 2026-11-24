import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "react-hot-toast";

import HomePage from "@/pages/HomePage";

import OverviewPage from "@/pages/app/OverviewPage";
import PhotosPage from "@/pages/app/PhotosPage";
import ObjectsPage from "@/pages/app/ObjectsPage";
import ObjectDetailPage from "@/pages/app/ObjectDetailPage";
import SpacesPage from "@/pages/app/SpacesPage";

export default function App() {
  return (
    <AuthProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            fontSize: "14px",
          },
        }}
      />

      <Routes>
        {/* Homepage */}
        <Route path="/" element={<HomePage />} />

        {/* Overview */}
        <Route path="/dashboard" element={<OverviewPage />} />

        {/* Photos */}
        <Route path="/dashboard/photos" element={<PhotosPage />} />

        {/* Objects */}
        <Route path="/dashboard/objects" element={<ObjectsPage />} />

        {/* Object Detail */}
        <Route
          path="/dashboard/objects/:id"
          element={<ObjectDetailPage />}
        />

        {/* Spaces */}
        <Route path="/dashboard/spaces" element={<SpacesPage />} />

        {/* Redirect nếu route không tồn tại */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}