import { useState } from 'react'
import ChapterViewer from './ChapterViewer'
import './styles.css'

function App() {
  const [currentChapter, setCurrentChapter] = useState(0)

  const handlePrevious = () => {
    setCurrentChapter(prev => Math.max(0, prev - 1))
  }

  const handleNext = () => {
    setCurrentChapter(prev => prev + 1)
  }

  return (
    <div className="app">
      <h1>Simple Viewer</h1>
      <div className="navigation">
        <button onClick={handlePrevious}>Previous</button>
        <span>Chapter {String(currentChapter).padStart(3, '0')}</span>
        <button onClick={handleNext}>Next</button>
      </div>
      <ChapterViewer chapterNumber={currentChapter} />
    </div>
  )
}

export default App
