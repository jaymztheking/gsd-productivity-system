import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import EngagePage from "./pages/EngagePage";
import IntakePage from "./pages/IntakePage";
import "./styles/index.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/engage" replace />} />
          <Route path="/engage" element={<EngagePage />} />
          <Route path="/intake" element={<IntakePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
