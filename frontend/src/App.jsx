import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SpeedInsights } from "@vercel/speed-insights/react";
import { AuthProvider } from "@/context/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { ROUTES } from "@/constants/routes";

import Splash from "@/pages/Splash";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import SymptomAnalysis from "@/pages/SymptomAnalysis";
import AnalysisResult from "@/pages/AnalysisResult";
import Passport from "@/pages/Passport";
import SOS from "@/pages/SOS";
import NotFound from "@/pages/NotFound";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path={ROUTES.SPLASH} element={<Splash />} />
          <Route path={ROUTES.LOGIN} element={<Login />} />

          <Route element={<AppShell />}>
            <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
            <Route path={ROUTES.SYMPTOM_ANALYSIS} element={<SymptomAnalysis />} />
            <Route path={ROUTES.ANALYSIS_RESULT} element={<AnalysisResult />} />
            <Route path={ROUTES.PASSPORT} element={<Passport />} />
            <Route path={ROUTES.SOS} element={<SOS />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
        <SpeedInsights />
      </BrowserRouter>
    </AuthProvider>
  );
}
