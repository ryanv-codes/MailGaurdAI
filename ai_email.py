"""
Professional Spam Email Detector - All-in-One Flask Application
Fixed: Logo display, Spam word highlighting, Animations
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import pickle
import re
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import gzip


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    MODEL_PATH = Path('model.pkl.gz')
    VECTORIZER_PATH = Path('vectorizer.pkl')
    MAX_TEXT_LENGTH = 50000
    MIN_TEXT_LENGTH = 10

    SPAM_KEYWORDS = [
        # Money & prizes
        'free', 'winner', 'cash', 'prize', 'congratulations', 'claim', 'won',
        'million', 'billion', 'thousand', 'dollars', 'money', 'earn',

        # Urgency
        'urgent', 'act now', 'limited time', 'expires', 'hurry', 'immediately',
        'act immediately', 'don\'t miss', 'last chance', 'ending soon',

        # Offers & deals
        'offer', 'discount', 'bonus', 'deal', 'sale', 'promotion',
        'guarantee', 'satisfaction guaranteed', 'risk-free', 'no obligation',
        '100% free', 'totally free', 'absolutely free', 'no cost',

        # Call to action
        'click here', 'click now', 'buy now', 'order now', 'call now',
        'visit', 'subscribe', 'unsubscribe', 'download', 'install',

        # Suspicious content
        'viagra', 'pharmacy', 'pills', 'medication', 'prescription',
        'loan', 'credit', 'debt', 'mortgage', 'insurance',
        'investment', 'opportunity', 'income', 'profit',
        'work from home', 'make money', 'earn money', 'extra income', 'mlm',

        # Weight & health
        'weight loss', 'lose weight', 'diet', 'fat', 'slim',
        'enlargement', 'enhancement', 'growth',

        # Gambling & lottery
        'casino', 'lottery', 'sweepstakes', 'jackpot', 'betting',

        # Suspicious phrases
        'no questions asked', 'confidential', 'secret', 'hidden',
        'limited supply', 'while supplies last', 'one time',
        'dear friend', 'dear sir', 'dear madam',
        'meet singles', 'dating', 'lonely',

        # Exclusive & special
        'exclusive', 'special offer', 'selected', 'chosen', 'qualified',

        # Additional common spam words
        'amazing', 'incredible', 'unbelievable', 'miracle',
        'breakthrough', 'revolutionary', 'shocking',
        'congratulation', 'felicitations', 'you have been selected',
        'claim your', 'accept', 'approval', 'pending'
    ]

# Load ML models
model = None
vectorizer = None

try:
    if Config.MODEL_PATH.exists() and Config.VECTORIZER_PATH.exists():
        # model.pkl.gz ko gzip ke through load karo
        with gzip.open(Config.MODEL_PATH, 'rb') as f:
            model = pickle.load(f)

        # vectorizer normal pickle se hi rahega
        with open(Config.VECTORIZER_PATH, 'rb') as f:
            vectorizer = pickle.load(f)

        logger.info(f"✓ Model loaded from {Config.MODEL_PATH}")
        logger.info(f"✓ Vectorizer loaded from {Config.VECTORIZER_PATH}")
    else:
        logger.warning(f"⚠ Model files not found. Expected: {Config.MODEL_PATH} and {Config.VECTORIZER_PATH}")
        logger.warning("⚠ Using fallback heuristic detection.")
except Exception as e:
    logger.error(f"✗ Error loading models: {e}", exc_info=True)
    model = None
    vectorizer = None



def preprocess_text(text: str) -> str:
    """Clean and normalize text for ML model"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def find_spam_keywords(text: str) -> List[str]:
    """Find spam trigger words in text"""
    text_lower = text.lower()
    found = []

    for keyword in Config.SPAM_KEYWORDS:
        # Handle multi-word phrases differently
        if ' ' in keyword:
            # For phrases, use simple case-insensitive search
            if keyword.lower() in text_lower:
                found.append(keyword)
        else:
            # For single words, use word boundary matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(keyword)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(found))


def calculate_features(text: str) -> Dict:
    """Extract spam-related features"""
    return {
        'length': len(text),
        'word_count': len(text.split()),
        'excessive_caps': sum(1 for c in text if c.isupper()) / max(len(text), 1) > 0.3,
        'excessive_punctuation': bool(re.search(r'[!?]{2,}', text)),
        'contains_url': bool(re.search(r'https?://|www\.', text)),
        'url_count': len(re.findall(r'https?://[^\s]+', text)),
        'contains_email': bool(re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)),
        'excessive_numbers': len(re.findall(r'\d+', text)) > 5,
        'money_symbols': len(re.findall(r'[$€£¥₹]', text))
    }


def heuristic_detection(keywords: List[str], features: Dict) -> Tuple[bool, float]:
    """Fallback spam detection using heuristics"""
    score = 0
    score += len(keywords) * 15
    score += min(features['url_count'] * 10, 30)
    score += 20 if features['excessive_caps'] else 0
    score += 15 if features['excessive_punctuation'] else 0
    score += min(features['money_symbols'] * 5, 15)

    confidence = min(score / 100, 0.99)
    is_spam = confidence >= 0.5

    return is_spam, confidence


# HTML Template - Fixed bugs
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Spam Email Detector - Protect Your Inbox</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #333;
      overflow-x: hidden;
    }

    nav {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      padding: 1.2rem 5%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 1000;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      animation: slideDown 0.5s ease;
    }

    @keyframes slideDown {
      from {
        transform: translateY(-100%);
        opacity: 0;
      }

      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 1.5rem;
      font-weight: 800;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .logo-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.5rem;
    }

    .nav-links {
      display: flex;
      gap: 2.5rem;
      align-items: center;
    }

    .nav-links a {
      color: #555;
      text-decoration: none;
      font-weight: 500;
      transition: all 0.3s;
      position: relative;
    }

    .nav-links a:hover {
      color: #667eea;
    }

    .nav-links a::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 0;
      height: 2px;
      background: #667eea;
      transition: width 0.3s;
    }

    .nav-links a:hover::after {
      width: 100%;
    }

    .hero {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 4rem 5%;
      position: relative;
      overflow: hidden;
    }

    .hero::before {
      content: '';
      position: absolute;
      width: 500px;
      height: 500px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      top: -250px;
      right: -250px;
      animation: float 6s ease-in-out infinite;
    }

    .hero::after {
      content: '';
      position: absolute;
      width: 400px;
      height: 400px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      bottom: -200px;
      left: -200px;
      animation: float 8s ease-in-out infinite;
    }

    @keyframes float {
      0%, 100% {
        transform: translateY(0px);
      }
      50% {
        transform: translateY(-20px);
      }
    }

    .hero-content {
      max-width: 1400px;
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4rem;
      align-items: center;
      z-index: 1;
    }

    .hero-text {
      animation: fadeInLeft 0.8s ease;
    }

    @keyframes fadeInLeft {
      from {
        opacity: 0;
        transform: translateX(-50px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .badge {
      display: inline-block;
      padding: 0.5rem 1.2rem;
      background: rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(10px);
      border-radius: 50px;
      color: white;
      font-weight: 600;
      font-size: 0.85rem;
      letter-spacing: 1px;
      margin-bottom: 1.5rem;
    }

    h1 {
      font-size: 3.5rem;
      color: white;
      margin-bottom: 1.5rem;
      line-height: 1.2;
      font-weight: 800;
    }

    .hero-subtitle {
      font-size: 1.2rem;
      color: rgba(255, 255, 255, 0.9);
      margin-bottom: 2rem;
      line-height: 1.6;
    }

    .cta-buttons {
      display: flex;
      gap: 1rem;
    }

    .btn-primary {
      padding: 1rem 2.5rem;
      background: white;
      color: #667eea;
      border: none;
      border-radius: 12px;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }

    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    }

    .btn-secondary {
      padding: 1rem 2.5rem;
      background: transparent;
      color: white;
      border: 2px solid white;
      border-radius: 12px;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s;
    }

    .btn-secondary:hover {
      background: white;
      color: #667eea;
    }

    .detector-card {
      background: white;
      border-radius: 24px;
      padding: 2.5rem;
      box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3);
      animation: fadeInRight 0.8s ease;
    }

    @keyframes fadeInRight {
      from {
        opacity: 0;
        transform: translateX(50px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .input-methods {
      display: flex;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .input-method-btn {
      flex: 1;
      padding: 0.8rem;
      background: #f5f5f5;
      border: 2px solid transparent;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .input-method-btn.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-color: #667eea;
    }

    .input-method-btn:hover {
      transform: translateY(-2px);
    }

    textarea {
      width: 100%;
      min-height: 200px;
      padding: 1.5rem;
      border: 2px solid #e0e0e0;
      border-radius: 16px;
      font-size: 1rem;
      font-family: 'inter';
      resize: vertical;
      transition: all 0.3s;
      margin-bottom: 1rem;
    }

    textarea:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
    }

    .file-upload {
      display: none;
    }

    .file-upload-area {
      display: none;
      border: 2px dashed #e0e0e0;
      border-radius: 16px;
      padding: 3rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s;
      margin-bottom: 1rem;
    }

    .file-upload-area.show {
      display: block;
    }

    .file-upload-area:hover {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.05);
    }

    .file-upload-area.dragover {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.1);
    }

    .check-btn {
      width: 100%;
      padding: 1.2rem;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 16px;
      font-weight: 700;
      font-size: 1.1rem;
      cursor: pointer;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .check-btn:hover:not(:disabled) {
      transform: translateY(-3px);
      box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
    }

    .check-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .examples {
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid #e0e0e0;
    }

    .examples-title {
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 0.8rem;
      font-weight: 600;
    }

    .example-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .example-tag {
      padding: 0.5rem 1rem;
      background: #f0f0f0;
      border-radius: 20px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.3s;
    }

    .example-tag:hover {
      background: #667eea;
      color: white;
      transform: translateY(-2px);
    }

    .results-container {
      max-width: 1400px;
      margin: 4rem auto;
      padding: 0 5%;
      display: none;
    }

    .results-container.show {
      display: block;
      animation: fadeIn 0.5s ease;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    .result-card {
      background: white;
      border-radius: 24px;
      padding: 3rem;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
      margin-bottom: 2rem;
    }

    .result-header {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 2rem;
      padding-bottom: 2rem;
      border-bottom: 2px solid #f0f0f0;
    }

    .result-icon {
      width: 80px;
      height: 80px;
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
      animation: scaleIn 0.5s ease;
    }

    @keyframes scaleIn {
      from {
        transform: scale(0);
        opacity: 0;
      }
      to {
        transform: scale(1);
        opacity: 1;
      }
    }

    .result-icon.spam {
      background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    }

    .result-icon.safe {
      background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
    }

    .result-info h2 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }

    .confidence-bar {
      width: 100%;
      height: 8px;
      background: #f0f0f0;
      border-radius: 10px;
      overflow: hidden;
      margin-top: 1rem;
    }

    .confidence-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      border-radius: 10px;
      transition: width 1s ease;
    }

    .spam-words-section {
      margin-top: 2rem;
    }

    .section-title {
      font-size: 1.3rem;
      font-weight: 700;
      margin-bottom: 1rem;
      color: #333;
    }

    .spam-words-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 0.8rem;
      margin-bottom: 1.5rem;
    }

    .spam-word-tag {
      padding: 0.6rem 1.2rem;
      background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
      color: white;
      border-radius: 20px;
      font-weight: 600;
      font-size: 0.9rem;
      animation: popIn 0.3s ease;
    }

    @keyframes popIn {
      from {
        transform: scale(0);
        opacity: 0;
      }
      to {
        transform: scale(1);
        opacity: 1;
      }
    }

    .highlighted-text {
      background: #f8f9fa;
      padding: 2rem;
      border-radius: 16px;
      border-left: 4px solid #667eea;
      font-family: 'inter';
      line-height: 1.8;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .highlighted-text mark {
      background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
      color: white;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
    }

    .analysis-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-top: 2rem;
    }

    .analysis-item {
      background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
      padding: 1.5rem;
      border-radius: 16px;
      border-left: 4px solid #667eea;
    }

    .analysis-label {
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 0.5rem;
    }

    .analysis-value {
      font-size: 1.5rem;
      font-weight: 700;
      color: #333;
    }

    .how-it-works {
      background: white;
      padding: 6rem 5%;
    }

    .section-header {
      text-align: center;
      margin-bottom: 4rem;
    }

    .section-header h2 {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      color: #333;
    }

    .section-header p {
      font-size: 1.1rem;
      color: #666;
      max-width: 600px;
      margin: 0 auto;
    }

    .steps-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 3rem;
      max-width: 1200px;
      margin: 0 auto;
    }

    .step-card {
      text-align: center;
      padding: 2rem;
      transition: transform 0.3s;
      opacity: 0;
      transform: translateY(30px);
    }

    .step-card:hover {
      transform: translateY(-10px);
    }

    .step-number {
      width: 80px;
      height: 80px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1.5rem;
      font-size: 2rem;
      font-weight: 800;
      color: white;
    }

    .step-card h3 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      color: #333;
    }

    .step-card p {
      color: #666;
      line-height: 1.6;
    }

    .features {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 6rem 5%;
    }

    .features .section-header h2,
    .features .section-header p {
      color: white;
    }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }

    .feature-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      padding: 2.5rem;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all 0.3s;
      opacity: 0;
      transform: translateY(30px);
    }

    .feature-card:hover {
      transform: translateY(-10px);
      background: rgba(255, 255, 255, 0.15);
    }

    .feature-icon {
      font-size: 3rem;
      margin-bottom: 1.5rem;
    }

    .feature-card h3 {
      font-size: 1.3rem;
      margin-bottom: 1rem;
      color: white;
    }

    .feature-card p {
      color: rgba(255, 255, 255, 0.9);
      line-height: 1.6;
    }

    footer {
      background: #1a1a2e;
      color: white;
      padding: 4rem 5% 2rem;
    }

    .footer-content {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 3rem;
      margin-bottom: 3rem;
    }

    .footer-section h3 {
      margin-bottom: 1.5rem;
      font-size: 1.2rem;
    }

    .footer-section ul {
      list-style: none;
    }

    .footer-section ul li {
      margin-bottom: 0.8rem;
    }

    .footer-section ul li a {
      color: rgba(255, 255, 255, 0.7);
      text-decoration: none;
      transition: color 0.3s;
    }

    .footer-section ul li a:hover {
      color: white;
    }

    .footer-bottom {
      text-align: center;
      padding-top: 2rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.6);
    }

    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-top: 3px solid white;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }

    @media (max-width: 1024px) {
      .hero-content {
        grid-template-columns: 1fr;
        gap: 3rem;
      }

      h1 {
        font-size: 2.5rem;
      }

      .nav-links {
        display: none;
      }
    }

    @media (max-width: 768px) {
      h1 {
        font-size: 2rem;
      }

      .hero-subtitle {
        font-size: 1rem;
      }

      .cta-buttons {
        flex-direction: column;
      }

      .detector-card {
        padding: 1.5rem;
      }

      .result-header {
        flex-direction: column;
        text-align: center;
      }

      .section-header h2 {
        font-size: 2rem;
      }
    }
  </style>
</head>

<body>
  <nav>
    <div class="logo">
      <div class="logo-icon">🛡️</div>
      <span>SpamGuard AI</span>
    </div>
    <div class="nav-links">
      <a href="#hero">Home</a>
      <a href="#how-it-works">How It Works</a>
      <a href="#features">Features</a>
      <a href="#footer">Contact</a>
    </div>
  </nav>

  <section class="hero" id="hero">
    <div class="hero-content">
      <div class="hero-text">
        <div class="badge">🚀 POWERED BY AI</div>
        <h1>Detect Spam Emails Instantly with AI</h1>
        <p class="hero-subtitle">
          Protect your inbox with our advanced machine learning algorithm.
          Analyze any email content in seconds and get detailed insights on spam indicators.
        </p>
        <div class="cta-buttons">
          <button class="btn-primary"
            onclick="document.querySelector('.detector-card').scrollIntoView({behavior: 'smooth'})">
            Try It Now
          </button>
          <button class="btn-secondary"
            onclick="document.querySelector('#how-it-works').scrollIntoView({behavior: 'smooth'})">
            Learn More
          </button>
        </div>
      </div>

      <div class="detector-card">
        <div class="input-methods">
          <button class="input-method-btn active" onclick="switchInputMethod('text')">
            📝 Text Input
          </button>
          <button class="input-method-btn" onclick="switchInputMethod('file')">
            📁 File Upload
          </button>
        </div>

        <textarea id="emailInput" placeholder="Paste your email content here...

Example: Try pasting a promotional email or suspicious message..."></textarea>

        <div class="file-upload-area" id="fileUploadArea">
          <div style="font-size: 3rem; margin-bottom: 1rem;">📂</div>
          <h3>Drop your file here</h3>
          <p style="color: #666; margin-top: 0.5rem;">or click to browse (.txt, .eml files)</p>
          <input type="file" id="fileInput" class="file-upload" accept=".txt,.eml" onchange="handleFileSelect(event)">
        </div>

        <button class="check-btn" id="checkBtn" onclick="checkSpam()">
          <span id="btnText">🔍 Check for Spam</span>
        </button>

        <div class="examples">
          <div class="examples-title">Quick Test Examples:</div>
          <div class="example-tags">
            <span class="example-tag" onclick="loadExample('spam')">Spam Example</span>
            <span class="example-tag" onclick="loadExample('safe')">Safe Example</span>
            <span class="example-tag" onclick="loadExample('clear')">Clear</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <div class="results-container" id="resultsContainer">
    <div class="result-card">
      <div class="result-header">
        <div class="result-icon" id="resultIcon"></div>
        <div class="result-info">
          <h2 id="resultTitle"></h2>
          <p id="resultDescription"></p>
          <div class="confidence-bar">
            <div class="confidence-fill" id="confidenceFill"></div>
          </div>
          <p style="margin-top: 0.5rem; color: #666;" id="confidenceText"></p>
        </div>
      </div>

      <div id="spamWordsSection" style="display: none;">
        <div class="section-title">🎯 Spam Keywords Detected</div>
        <div class="spam-words-grid" id="spamWordsGrid"></div>

        <div style="margin-top: 2rem;">
          <div class="section-title">📄 Highlighted Analysis</div>
          <div class="highlighted-text" id="highlightedText"></div>
        </div>
      </div>

      <div class="section-title" style="margin-top: 2rem;">📊 Detailed Analysis</div>
      <div class="analysis-grid" id="analysisGrid"></div>
    </div>
  </div>

  <section class="how-it-works" id="how-it-works">
    <div class="section-header">
      <h2>How It Works</h2>
      <p>Our AI-powered spam detector uses advanced machine learning to analyze email content</p>
    </div>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-number">1</div>
        <h3>Input Email</h3>
        <p>Paste your email content or upload a file. Our system accepts various formats including plain text and .eml
          files.</p>
      </div>
      <div class="step-card">
        <div class="step-number">2</div>
        <h3>AI Analysis</h3>
        <p>Our trained machine learning model analyzes the content, identifying spam patterns, suspicious keywords, and
          phishing indicators.</p>
      </div>
      <div class="step-card">
        <div class="step-number">3</div>
        <h3>Get Results</h3>
        <p>Receive instant results with confidence scores, highlighted spam words, and actionable recommendations.</p>
      </div>
    </div>
  </section>

  <section class="features" id="features">
    <div class="section-header">
      <h2>Powerful Features</h2>
      <p>Everything you need to protect your inbox from spam and phishing</p>
    </div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <h3>AI-Powered Detection</h3>
        <p>Advanced machine learning algorithms trained on millions of emails for accurate spam detection.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <h3>Instant Results</h3>
        <p>Get spam analysis in milliseconds with real-time processing and immediate feedback.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <h3>Keyword Highlighting</h3>
        <p>Identifies and highlights suspicious words and phrases that trigger spam filters.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>Detailed Analytics</h3>
        <p>Comprehensive analysis including confidence scores, word count, and spam indicators.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <h3>Privacy First</h3>
        <p>Your emails are analyzed in real-time and never stored on our servers.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📱</div>
        <h3>Mobile Friendly</h3>
        <p>Works seamlessly on all devices - desktop, tablet, and mobile phones.</p>
      </div>
    </div>
  </section>

  <footer id="footer">
    <div class="footer-content">
      <div class="footer-section">
        <h3>SpamGuard AI</h3>
        <p style="color: rgba(255, 255, 255, 0.7); line-height: 1.6;">
          Protecting inboxes worldwide with cutting-edge AI technology. Detect spam, phishing, and malicious emails
          instantly.
        </p>
      </div>
      <div class="footer-section">
        <h3>Quick Links</h3>
        <ul>
          <li><a href="#hero">Home</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#features">Features</a></li>
          <li><a href="#hero">Try Demo</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Resources</h3>
        <ul>
          <li><a href="#">Documentation</a></li>
          <li><a href="#">API Access</a></li>
          <li><a href="#">Privacy Policy</a></li>
          <li><a href="#">Terms of Service</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Connect</h3>
        <ul>
          <li><a href="#">GitHub</a></li>
          <li><a href="#">Twitter</a></li>
          <li><a href="#">LinkedIn</a></li>
          <li><a href="#">Contact Us</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2024 SpamGuard AI. All rights reserved. Built with ❤️ for a safer internet.</p>
    </div>
  </footer>

  <script>
    function switchInputMethod(method) {
      const textArea = document.getElementById('emailInput');
      const fileArea = document.getElementById('fileUploadArea');
      const buttons = document.querySelectorAll('.input-method-btn');

      buttons.forEach(btn => btn.classList.remove('active'));

      if (method === 'text') {
        textArea.style.display = 'block';
        fileArea.classList.remove('show');
        buttons[0].classList.add('active');
      } else {
        textArea.style.display = 'none';
        fileArea.classList.add('show');
        buttons[1].classList.add('active');
      }
    }

    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');

    fileUploadArea.addEventListener('click', () => fileInput.click());

    fileUploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      fileUploadArea.classList.add('dragover');
    });

    fileUploadArea.addEventListener('dragleave', () => {
      fileUploadArea.classList.remove('dragover');
    });

    fileUploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      fileUploadArea.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file) {
        readFile(file);
      }
    });

    function handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        readFile(file);
      }
    }

    function readFile(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        document.getElementById('emailInput').value = content;
        switchInputMethod('text');
        showNotification('File loaded successfully! Click "Check for Spam" to analyze.', 'success');
      };
      reader.onerror = () => {
        showNotification('Error reading file. Please try again.', 'error');
      };
      reader.readAsText(file);
    }

    const examples = {
      spam: `CONGRATULATIONS!!! You've WON $1,000,000 in our EXCLUSIVE lottery!

Click here NOW to claim your prize! This is a LIMITED TIME offer!

Act immediately! No questions asked! 100% FREE money!

Visit: www.totally-legit-lottery.com

This offer expires in 24 hours! Don't miss out!

Best regards,
International Lottery Commission`,

      safe: `Hello,

I hope this email finds you well. I wanted to follow up on our meeting last week regarding the project proposal.

I've attached the updated documentation for your review. Please let me know if you have any questions or need any clarifications.

Looking forward to hearing from you.

Best regards,
John Smith
Project Manager`
    };

    function loadExample(type) {
      const textarea = document.getElementById('emailInput');

      if (type === 'clear') {
        textarea.value = '';
        document.getElementById('resultsContainer').classList.remove('show');
        showNotification('Input cleared!', 'info');
      } else {
        textarea.value = examples[type];
        showNotification(`${type === 'spam' ? 'Spam' : 'Safe'} example loaded!`, 'info');
      }
    }

    async function checkSpam() {
      const emailInput = document.getElementById('emailInput');
      const checkBtn = document.getElementById('checkBtn');
      const btnText = document.getElementById('btnText');
      const text = emailInput.value.trim();

      if (!text) {
        showNotification('Please enter email content or upload a file', 'error');
        return;
      }

      checkBtn.disabled = true;
      btnText.innerHTML = '<div class="spinner"></div> Analyzing...';

      try {
        const response = await fetch('/api/check-spam', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();

        if (data.error) {
          showNotification('Error: ' + data.error, 'error');
          return;
        }

        displayResults(data, text);

        setTimeout(() => {
          document.getElementById('resultsContainer').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }, 300);

      } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to analyze email. Make sure the Flask server is running on port 5000.', 'error');
      } finally {
        checkBtn.disabled = false;
        btnText.innerHTML = '🔍 Check for Spam';
      }
    }

    function displayResults(data, originalText) {
      const resultsContainer = document.getElementById('resultsContainer');
      const resultIcon = document.getElementById('resultIcon');
      const resultTitle = document.getElementById('resultTitle');
      const resultDescription = document.getElementById('resultDescription');
      const confidenceFill = document.getElementById('confidenceFill');
      const confidenceText = document.getElementById('confidenceText');
      const spamWordsSection = document.getElementById('spamWordsSection');
      const spamWordsGrid = document.getElementById('spamWordsGrid');
      const highlightedText = document.getElementById('highlightedText');
      const analysisGrid = document.getElementById('analysisGrid');

      const isSpam = data.prediction === 'spam';
      const confidence = (data.confidence * 100).toFixed(1);

      resultIcon.className = `result-icon ${isSpam ? 'spam' : 'safe'}`;
      resultIcon.textContent = isSpam ? '⚠️' : '✅';

      resultTitle.textContent = isSpam ? 'SPAM DETECTED' : 'EMAIL IS SAFE';
      resultTitle.style.color = isSpam ? '#ff6b6b' : '#51cf66';

      resultDescription.textContent = isSpam
        ? 'This email contains spam indicators and should be treated with caution.'
        : 'This email appears to be legitimate with no significant spam indicators.';

      confidenceFill.style.width = confidence + '%';
      confidenceFill.style.background = isSpam
        ? 'linear-gradient(90deg, #ff6b6b 0%, #ee5a6f 100%)'
        : 'linear-gradient(90deg, #51cf66 0%, #37b24d 100%)';
      confidenceText.textContent = `Confidence Score: ${confidence}%`;

      // Debug: Log the received data
      console.log('API Response:', data);
      console.log('Spam words received:', data.spam_words);
      console.log('Spam word count:', data.spam_word_count);

      // Always show spam words section if detected, regardless of prediction
      if (data.spam_words && data.spam_words.length > 0) {
        spamWordsSection.style.display = 'block';
        spamWordsGrid.innerHTML = data.spam_words
          .map((word, index) => `<div class="spam-word-tag" style="animation-delay: ${index * 0.05}s">${word}</div>`)
          .join('');

        // Highlight spam words in the text
        const highlighted = highlightSpamWords(originalText, data.spam_words);
        highlightedText.innerHTML = highlighted;
        
        console.log('Spam words section displayed with', data.spam_words.length, 'keywords');
        console.log('Highlighted text length:', highlighted.length);
      } else {
        spamWordsSection.style.display = 'none';
        console.log('No spam words detected - section hidden');
      }

      const wordCount = originalText.split(/\s+/).filter(w => w).length;
      const analysisItems = [
        { label: 'Total Words', value: wordCount, icon: '📝' },
        { label: 'Characters', value: originalText.length, icon: '🔤' },
        { label: 'Spam Indicators', value: data.spam_word_count || 0, icon: '🎯' },
        { label: 'Confidence', value: confidence + '%', icon: '📊' }
      ];

      if (data.features) {
        if (data.features.excessive_caps) {
          analysisItems.push({ label: 'Excessive Caps', value: 'Detected', icon: '⚠️' });
        }
        if (data.features.excessive_punctuation) {
          analysisItems.push({ label: 'Excessive Punctuation', value: 'Detected', icon: '❗' });
        }
        if (data.features.contains_url) {
          analysisItems.push({ label: 'Contains URL', value: 'Yes', icon: '🔗' });
        }
      }

      analysisGrid.innerHTML = analysisItems
        .map(item => `
          <div class="analysis-item">
            <div class="analysis-label">${item.icon} ${item.label}</div>
            <div class="analysis-value">${item.value}</div>
          </div>
        `).join('');

      resultsContainer.classList.add('show');
    }

    function highlightSpamWords(text, spamWords) {
      if (!text || !spamWords || spamWords.length === 0) {
        return text;
      }

      let highlighted = text;
      
      // Sort spam words by length (longest first) to avoid partial matches
      const sortedWords = [...spamWords].sort((a, b) => b.length - a.length);

      sortedWords.forEach(word => {
        // Create a case-insensitive regex pattern for whole word matching
        const escapedWord = escapeRegex(word);
        const regex = new RegExp('\\b(' + escapedWord + ')\\b', 'gi');
        
        // Replace with marked text, preserving original case
        highlighted = highlighted.replace(regex, '<mark>$1</mark>');
      });

      console.log('Highlighting complete. Marked words:', spamWords.length);
      return highlighted;
    }

    function escapeRegex(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\        <div class="result-icon" id="resultIcon"></div>');
    }

    function showNotification(message, type) {
      const existing = document.querySelector('.notification');
      if (existing) {
        existing.remove();
      }

      const notification = document.createElement('div');
      notification.className = 'notification';
      notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#667eea'};
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        font-weight: 600;
      `;
      notification.textContent = message;

      const style = document.createElement('style');
      style.textContent = `
        @keyframes slideInRight {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `;
      document.head.appendChild(style);

      document.body.appendChild(notification);

      setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
      }, 3000);
    }

    document.getElementById('emailInput').addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        checkSpam();
      }
    });

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, observerOptions);

    // Observe all animated elements
    document.querySelectorAll('.step-card, .feature-card').forEach(el => {
      el.style.transition = 'all 0.6s ease';
      observer.observe(el);
    });
  </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/check-spam', methods=['POST'])
def check_spam():
    """API endpoint to analyze text for spam"""
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                "error": "Please provide 'text' in the request body"
            }), 400

        text = data['text'].strip()

        if not text:
            return jsonify({
                "error": "Text cannot be empty"
            }), 400

        if len(text) < Config.MIN_TEXT_LENGTH:
            return jsonify({
                "error": f"Text must be at least {Config.MIN_TEXT_LENGTH} characters"
            }), 400

        if len(text) > Config.MAX_TEXT_LENGTH:
            return jsonify({
                "error": f"Text exceeds maximum length of {Config.MAX_TEXT_LENGTH} characters"
            }), 400

        spam_keywords = find_spam_keywords(text)
        features = calculate_features(text)

        # Debug logging
        logger.info(f"Text length: {len(text)} characters")
        logger.info(f"Spam keywords found: {len(spam_keywords)} - {spam_keywords[:10]}")  # Show first 10

        if model is not None and vectorizer is not None:
            processed_text = preprocess_text(text)
            text_vectorized = vectorizer.transform([processed_text])
            prediction = model.predict(text_vectorized)[0]

            try:
                prediction_proba = model.predict_proba(text_vectorized)[0]
                confidence = float(max(prediction_proba))
            except AttributeError:
                confidence = 1.0 if prediction == 1 else 0.8

            is_spam = bool(prediction)
        else:
            is_spam, confidence = heuristic_detection(spam_keywords, features)

        result = {
            "prediction": "spam" if is_spam else "not spam",
            "confidence": confidence,
            "spam_words": spam_keywords,
            "spam_word_count": len(spam_keywords),
            "features": features,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "model_used": model is not None
        }

        logger.info(f"Analysis: {result['prediction']} (confidence: {confidence:.2%})")

        return jsonify(result)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred during analysis"
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🛡️  SPAMGUARD AI - PROFESSIONAL SPAM DETECTOR")
    print("=" * 70)

    if model is not None and vectorizer is not None:
        print("✓ ML Model: Loaded successfully from", Config.MODEL_PATH)
        print("✓ Vectorizer: Loaded successfully from", Config.VECTORIZER_PATH)
        print("✓ Detection Mode: Machine Learning")
    else:
        print("⚠ ML Model: Not loaded (using heuristic fallback)")
        print(f"⚠ Make sure '{Config.MODEL_PATH.name}' and '{Config.VECTORIZER_PATH.name}' are in the same folder")
        print("✓ Detection Mode: Heuristic (keyword-based)")

    print("\n🌐 Server starting at: http://localhost:5000")
    print("📊 Health check: http://localhost:5000/api/health")
    print("🔌 API endpoint: http://localhost:5000/api/check-spam")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
