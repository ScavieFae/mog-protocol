import { BrowserRouter, Routes, Route } from "react-router-dom"
import { BoardPage } from "@/pages/BoardPage"
import { GardenPage } from "@/pages/GardenPage"
import { TrinityPage } from "@/pages/TrinityPage"
import { ServiceDetailPage } from "@/pages/ServiceDetailPage"
import { ConnectPage } from "@/pages/ConnectPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route path="/garden" element={<GardenPage />} />
        <Route path="/service/:id" element={<ServiceDetailPage />} />
        <Route path="/connect" element={<ConnectPage />} />
        <Route path="/colony" element={<TrinityPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
