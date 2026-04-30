import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DocumentDetail from './pages/DocumentDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
