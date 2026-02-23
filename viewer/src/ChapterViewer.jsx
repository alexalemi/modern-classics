import { useState, useEffect } from 'react'

function ChapterViewer({ chapterNumber }) {
  const [originalText, setOriginalText] = useState('')
  const [modernText, setModernText] = useState('')
  const [explanation, setExplanation] = useState('')

  useEffect(() => {
    const chapterNum = String(chapterNumber).padStart(3, '0')

        // Load original text
    fetch(`/chapters/${chapterNum}.txt`)
      .then(async res => {
        if (!res.ok) {
          throw new Error(`Chapter not found (Status: ${res.status})`);
        }
        const text = await res.text();
        // Check if we got back HTML (which would indicate a fallback to index.html)
        if (text.includes('<!DOCTYPE html>') || text.includes('<html')) {
          throw new Error('Chapter not found');
        }
        return text;
      })
      .then(text => {
        console.log('Original text received:', text);
        if (!text.trim()) {
          throw new Error('Empty chapter content');
        }
        // Remove any HTML tags if present
        const cleanText = text.replace(/<[^>]*>/g, '');
        setOriginalText(cleanText || 'No content available');
      })
      .catch(error => {
        console.error('Error loading chapter:', error);
        setOriginalText(`Error: ${error.message}`);
      })


    // Load modern text and explanation
    fetch(`/modern_chapters/${chapterNum}.txt`)
      .then(res => res.text())
      .then(text => {
        const modernMatch = text.match(/<modernized_text>(.*?)<\/modernized_text>/s)
        const explanationMatch = text.match(/<explanation>(.*?)<\/explanation>/s)
        
        setModernText(modernMatch ? modernMatch[1].trim() : 'Not found')
        setExplanation(explanationMatch ? explanationMatch[1].trim() : 'Not found')
      })
      .catch(() => {
        setModernText('Chapter not found')
        setExplanation('Not found')
      })
  }, [chapterNumber])

  return (
    <div className="chapter-viewer">
      <div className="text-container">
        <div className="modern">
          <h2>Modern Text</h2>
          <div className="text-content">{modernText}</div>
        </div>
        <div className="original">
          <h2>Original Text</h2>
          <div className="text-content">{originalText}</div>
        </div>
      </div>
      <div className="explanation">
        <h2>Explanation</h2>
        <div className="text-content">{explanation}</div>
      </div>
    </div>
  )
}

export default ChapterViewer