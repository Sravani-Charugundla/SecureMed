import React, { useState, useEffect } from 'react';
import { model } from './mainmodule.js';
import { useLocation } from 'react-router-dom';
import Tesseract from 'tesseract.js';

function ChatApp() {
  const location = useLocation();
  const [inputText, setInputText] = useState('');
  const [chatMessages, setChatMessages] = useState([]);

  const [convertedText, setConvertedText] = useState('');
  var finalval='';

useEffect(() => {
    const getInitialResponse = async () => {
      const ff = sessionStorage.getItem("myanalyseimage");
      if (!ff) return;
      
      Tesseract.recognize(ff)
          .then(async ({ data: { text } }) => {
              console.log("Recognized Text:", text);
              setConvertedText(text);
              
              // Send text to Flask backend
              try {
                const response = await fetch('http://localhost:5000/api/process-text', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({ text }),
                });
                
                const result = await response.json();
                console.log('RAG processing result:', result);
                
                // Continue with your existing chat logic
                console.log(text)
                const defaultPrompt = text;
                appendUserMessage(defaultPrompt);
                const modelResult = await model.generateContent(defaultPrompt);
                const modelResponse = await modelResult.response.text();
                appendBotMessage(modelResponse.trim());
              } catch (error) {
                console.error('Error processing text:', error);
                appendErrorMessage("Error processing text. Please try again.");
              }
          })
          .catch(error => {
              console.error("Error recognizing text:", error);
          });
    };

    getInitialResponse();
  }, []);





  

  const getChatResponse = async () => {
    const userText = inputText.trim();
    if (!userText) return;

    appendUserMessage(userText);

    try {
      // First, query our RAG system
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userText }),
      });
      
      const result = await response.json();
      
      if (result.error) {
        // If RAG system fails, fallback to the model
        const modelResult = await model.generateContent(userText);
        const modelResponse = await modelResult.response.text();
        appendBotMessage(modelResponse.trim());
      } else {
        // Use the RAG system's response
        appendBotMessage(result.answer);
      }
    } catch (error) {
      appendErrorMessage("Oops! Something went wrong while retrieving the response. Please try again.");
    }
    setInputText('');
  };

  const appendUserMessage = (message) => {
    setChatMessages(prevMessages => [
      ...prevMessages,
      { type: 'user', text: message }
    ]);
  };

  const appendBotMessage = (message) => {
    setChatMessages(prevMessages => [
      ...prevMessages,
      { type: 'bot', text: message }
    ]);
  };

  const appendErrorMessage = (errorMessage) => {
    setChatMessages(prevMessages => [
      ...prevMessages,
      { type: 'error', text: errorMessage }
    ]);
  };

  return (
    <div className="container-fluid h-100 bg-tertiary">
      <div className="row justify-content-center h-100 border">
        <div className="col-md-8 col-lg-8 chat-container h-100">
          {chatMessages.map((message, index) => (
            <div key={index} className={`${message.type}-message-container`}>
              <p className={`${message.type}-message`}>
                <ul className="list-unstyled">
                  {message.text.split('\n').map((line, index) => (
                    <li key={index}>
                      {line.startsWith('**') ? <strong>{line.substring(2)}</strong> : line}
                    </li>
                  ))}
                </ul>
              </p>
            </div>
          ))}
        </div>
      </div>
      <div className="row fixed-bottom mb-3">
        <div className="col">
          <div className="typing-container">
            <textarea
              className='form-control'
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && window.innerWidth > 800) {
                  e.preventDefault();
                  getChatResponse();
                }
              }}
              spellCheck="false"
              placeholder="Enter a prompt here"
              required
            ></textarea>
            <button
              id="send-btn"
              className="btn btn-primary mt-2"
              onClick={getChatResponse}
            ><i class="fa-solid fa-rocket"></i></button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatApp;
