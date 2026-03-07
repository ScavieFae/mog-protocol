import { BrowserRouter, Routes, Route } from "react-router-dom"
import { BoardPage } from "@/pages/BoardPage"
import { ServiceDetailPage } from "@/pages/ServiceDetailPage"
import { ConnectPage } from "@/pages/ConnectPage"
import { IntelPage } from "@/pages/IntelPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route path="/service/:id" element={<ServiceDetailPage />} />
        <Route path="/connect" element={<ConnectPage />} />
        <Route path="/intel" element={<IntelPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
