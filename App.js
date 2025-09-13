import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    handleFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleFile = (file) => {
    if (file && ['image/jpeg', 'image/png'].includes(file.type) && file.size <= 5 * 1024 * 1024) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setError(null);
      setProcessedImage(null);
    } else {
      setError('Invalid file. Only JPEG/PNG under 5MB allowed.');
    }
  };

  const handleSubmit = async () => {
    if (!image) return;
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', image);

    try {
      const response = await axios.post(`${backendUrl}/remove-background`, formData, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      setProcessedImage(url);
    } catch (err) {
      setError(err.response?.data?.error || 'Error processing image.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (processedImage) {
      const link = document.createElement('a');
      link.href = processedImage;
      link.download = 'removed_bg_image.png';
      link.click();
    }
  };

  return (
    <div className="App">
      {/* Hero Section - SEO Optimized with Keywords */}
      <header className="hero">
        <h1>Free Online Background Remover - Remove BG from Image Instantly</h1>
        <p className="hero-desc">AI Clear BG is the best free online background remover tool. Remove background from image in seconds with AI-powered precision. Perfect for eCommerce, social media, and design projects. No signup required!</p>
        <div className="hero-buttons">
          <button className="cta-button" onClick={() => document.getElementById('upload').click()}>Start Removing Background</button>
          <button className="secondary-button">Watch Tutorial</button>
        </div>
      </header>

      {/* Features Section - For SEO Content */}
      <section className="features">
        <h2>Why Choose AI Clear BG for Background Removal?</h2>
        <div className="features-grid">
          <div className="feature">
            <h3>AI-Powered Accuracy</h3>
            <p>Our advanced AI removes backgrounds from any image automatically, handling hair, fur, and complex edges with premium quality.</p>
          </div>
          <div className="feature">
            <h3>100% Free & Fast</h3>
            <p>Remove background from image online for free. Process in under 5 seconds – no watermarks or limits.</p>
          </div>
          <div className="feature">
            <h3>Easy to Use</h3>
            <p>Upload JPEG or PNG, click remove, and download. Drag & drop support for seamless UX on desktop and mobile.</p>
          </div>
          <div className="feature">
            <h3>Premium Results</h3>
            <p>High-resolution output up to 25MP. Ideal for professional photos, product images, and creative edits.</p>
          </div>
        </div>
      </section>

      {/* Upload Section */}
      <section className="upload-section" onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}>
        <h2>Remove Background from Image - Upload Your Photo</h2>
        <div className="drop-zone">
          <label htmlFor="file-input">Drag & Drop or Click to Upload Image (JPEG/PNG, Max 5MB)</label>
          <input id="file-input" type="file" accept="image/jpeg,image/png" onChange={handleFileChange} />
          {preview && <img src={preview} alt="Preview - Original Image for Background Removal" className="preview" />}
        </div>
        <button className="process-button" onClick={handleSubmit} disabled={loading || !image}>
          {loading ? 'Processing with AI...' : 'Remove Background Now'}
        </button>
        {loading && <div className="loader">AI Magic in Progress...</div>}
        {error && <p className="error">{error}</p>}
      </section>

      {/* Results Section */}
      {processedImage && (
        <section className="result-section">
          <h2>Your Background Removed Image</h2>
          <div className="result">
            <img src={processedImage} alt="Processed Image - Background Removed" className="processed" />
            <button className="download-button" onClick={handleDownload}>Download PNG (Transparent BG)</button>
          </div>
          <p className="tip">Tip: Use this transparent PNG for overlays, product mockups, or social media posts!</p>
        </section>
      )}

      {/* FAQ Section - SEO Boost */}
      <section className="faq">
        <h2>Frequently Asked Questions - Online BG Remover</h2>
        <div className="faq-item">
          <h3>How to remove background from image online for free?</h3>
          <p>Upload your photo to AI Clear BG, click remove, and download the result instantly. It's 100% free!</p>
        </div>
        <div className="faq-item">
          <h3>Does this free background remover work on mobile?</h3>
          <p>Yes! Our tool is fully responsive and works on iOS, Android, and desktop browsers.</p>
        </div>
        <div className="faq-item">
          <h3>What file formats are supported?</h3>
          <p>JPEG and PNG up to 5MB. Output is always high-quality PNG with transparent background.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2025 AI Clear BG - Best Free Online Background Remover Tool. Powered by AI for Premium Results.</p>
        <p><a href="/privacy">Privacy Policy</a> | <a href="/terms">Terms of Service</a></p>
      </footer>
    </div>
  );
}

export default App;
