
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "react-hot-toast";

import HomePage from "@/pages/HomePage";
import OverviewPage from "@/pages/app/OverviewPage";
import PhotosPage from "@/pages/app/PhotosPage";

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
        <Route path="/" element={<HomePage />} />

        <Route path="/dashboard" element={<OverviewPage />} />

        <Route
          path="/dashboard/photos"
          element={<PhotosPage />}
        />

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </AuthProvider>
  );
}
