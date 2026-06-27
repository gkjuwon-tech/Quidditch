import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import Embers from "./components/Embers";
import Home from "./pages/Home";
import Engineering from "./pages/Engineering";
import Codex from "./pages/Codex";
import Fund from "./pages/Fund";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <div className="grain vignette relative min-h-screen">
      <Embers />
      <Nav />
      <ScrollToTop />
      <main className="relative z-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/engineering" element={<Engineering />} />
          <Route path="/codex" element={<Codex />} />
          <Route path="/fund" element={<Fund />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
