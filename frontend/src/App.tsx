import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './features/dashboard/Dashboard'
import Curriculum from './features/course/Curriculum'
import Library from './features/library/Library'
import Vocabulary from './features/vocab/Vocabulary'
import MaterialDetail from './features/material/MaterialDetail'
import Review from './features/review/Review'
import ImportPage from './features/importer/ImportPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="course" element={<Curriculum />} />
        <Route path="library" element={<Library />} />
        <Route path="vocab" element={<Vocabulary />} />
        <Route path="materials/:id" element={<MaterialDetail />} />
        <Route path="review" element={<Review />} />
        <Route path="import" element={<ImportPage />} />
      </Route>
    </Routes>
  )
}
