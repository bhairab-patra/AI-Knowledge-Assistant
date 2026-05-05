
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ConfirmDialog from './component/ConfirmDialog';
import Tooltip from './component/Tooltip';
import './ChatApp.css';
import logger from './utils/logger';
import api, { getViewUrl } from './services/api';
import rehypeSanitize from 'rehype-sanitize';

export default function ChatApp({ chatSessionId }) {

  const TRUNCATE_TITLE = 30;
  const FEEDBACK_CONFIRM_MS = 2000;
  const MAX_FEEDBACK_CHARS = 500;
  const MIN_INPUT_LENGTH = 3;
  const TEXTAREA_MIN_HEIGHT = 75;
  const TEXTAREA_MAX_HEIGHT = 120;
  const CHAT_WINDOW_HEIGHT = 600;
  const CHAT_WINDOW_WIDTH = 400;
  const MINIMIZED_SIZE = 100;
  const WIDGET_VERSION = 'v1.1.0';

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! How can I help you today?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);
  const [sessionId, setSessionId] = useState(null);
  const [chatUrl, setChatUrl] = useState(null);
  const [feedbackMap, setFeedbackMap] = useState({});
  const [isThinking, setIsThinking] = useState(false);
  const [expandedFeedback, setExpandedFeedback] = useState(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [expandedSources, setExpandedSources] = useState({});
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [assistantTitle, setAssistantTitle] = useState('Ask AI Assistant');
  const [headerColor, setHeaderColor] = useState('');
  const [primaryColor, setPrimaryColor] = useState('');
  const [fontFamily, setFontFamily] = useState("'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif");
  const [sessionError, setSessionError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [currentSessionMessageCount, setCurrentSessionMessageCount] = useState(1);
  const [hasUserSentMessage, setHasUserSentMessage] = useState(false);
  const [showMinimize, setShowMinimize] = useState(true);
  const [showScrollDown, setShowScrollDown] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [reloadingIndex, setReloadingIndex] = useState(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [previewHistoryId, setPreviewHistoryId] = useState(null);
  const [isOverflowOpen, setIsOverflowOpen] = useState(false);

  const HISTORY_STORAGE_KEY = 'aika_chat_history_v1';
  const MAX_HISTORY_ITEMS = 30;

  const MAX_CHARS = 2000;

  const ERROR_TYPES = {
    SESSION_EXPIRED: { code: 'SESSION_EXPIRED', message: 'Session expired. Please close and try again.', recoverable: false },
    SESSION_NOT_FOUND: { code: 'SESSION_NOT_FOUND', message: 'Session not found. Please close and try again.', recoverable: false },
    AUTH_FAILED: { code: 'AUTH_FAILED', message: 'Authentication failed. Please close and try again.', recoverable: false },
    NETWORK_ERROR: { code: 'NETWORK_ERROR', message: 'Connection issue or Session expired. Please try again.', recoverable: true },
    SERVER_ERROR: { code: 'SERVER_ERROR', message: 'Something went wrong. Please try again.', recoverable: true },
    UNKNOWN: { code: 'UNKNOWN', message: 'Session not found. Please close and try again.', recoverable: false },
  };

  const classifyHttpError = (status) => {
    if (status === 401) return ERROR_TYPES.AUTH_FAILED;
    if (status === 403) return ERROR_TYPES.SESSION_EXPIRED;
    if (status === 404) return ERROR_TYPES.SESSION_NOT_FOUND;
    if (status >= 500) return ERROR_TYPES.SERVER_ERROR;
    return ERROR_TYPES.UNKNOWN;
  };



  // Auto-scroll to bottom
  const scrollToBottom = (behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);


  useEffect(() => {
    if (
      chatSessionId &&
      chatSessionId !== null &&
      chatSessionId !== 'null' &&
      typeof chatSessionId === 'string' &&
      chatSessionId.trim().length > 0
    ) {
      // Fetch session details from backend
      fetchSessionDetails(chatSessionId);

    } else {
      logger.warn('Invalid session - not opening')
      setIsOpen(false);
    }
  }, [chatSessionId]);


  useEffect(() => {
    const htmlElement = document.documentElement;
    const bodyElement = document.body;

    const setSize = (h, w) => {
      htmlElement.style.height = typeof h === 'string' ? h : `${h}px`;
      htmlElement.style.width = typeof w === 'string' ? w : `${w}px`;
      bodyElement.style.height = typeof h === 'string' ? h : `${h}px`;
      bodyElement.style.width = typeof w === 'string' ? w : `${w}px`;
      bodyElement.style.pointerEvents = 'auto';
    };

    if (isMinimized) {
      setSize(MINIMIZED_SIZE, MINIMIZED_SIZE);
      if (window.parent !== window) {
        window.parent.postMessage({
          type: 'CHANGE_IFRAME_HEIGHT',
          height: MINIMIZED_SIZE,
          width: MINIMIZED_SIZE,
          mode: 'minimized'
        }, '*');
      }
    } else if (isMaximized && isOpen) {
      // Full screen / full width
      const maxW = window.screen?.availWidth || window.innerWidth || 1200;
      const maxH = window.screen?.availHeight || window.innerHeight || 800;
      setSize('100vh', '100vw');
      if (window.parent !== window) {
        window.parent.postMessage({
          type: 'CHANGE_IFRAME_HEIGHT',
          height: maxH,
          width: maxW,
          mode: 'maximized'
        }, '*');
      }
    } else if (isOpen) {
      setSize(CHAT_WINDOW_HEIGHT, CHAT_WINDOW_WIDTH);
      if (window.parent !== window) {
        window.parent.postMessage({
          type: 'CHANGE_IFRAME_HEIGHT',
          height: CHAT_WINDOW_HEIGHT,
          width: CHAT_WINDOW_WIDTH,
          mode: 'normal'
        }, '*');
      }
    }
  }, [isMinimized, isMaximized, isOpen]);


  // useEffect(() => {
  //   const handleVisibilityChange = async () => {
  //     if (document.visibilityState === 'visible' && sessionId && isOpen) {
  //       try {
  //         const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
  //           method: 'GET',
  //           headers: { 'Content-Type': 'application/json' }
  //         });
  //         const data = await response.json();
  //         if (!response.ok || data.status !== 'active') {
  //           setSessionError('Session expired or invalid. Please close and try again.');
  //           setIsOpen(false);
  //         }
  //       } catch (error) {
  //         console.error('Session revalidation failed:', error);
  //       }
  //     }
  //   };

  //   document.addEventListener('visibilitychange', handleVisibilityChange);
  //   return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  // }, [sessionId, isOpen]);


  const fetchSessionDetails = async (sessionId) => {
    setIsLoading(true);
    try {
      const response = await api.getSession(sessionId);
      logger.info('api.getSession(sessionId)')
      const data = await response.json();
      if (response.ok && data.status === "active") {
        setSessionError(null);
        setSessionId(sessionId);

        let restoredMessages;

        if (data.conversationHistory && data.conversationHistory.length > 0) {
          restoredMessages = [
            { role: 'assistant', content: 'Hi! How can I help you today?' },
            ...data.conversationHistory
          ];

        } else {
          restoredMessages = [{ role: 'assistant', content: 'Hi! How can I help you today?' }];
        }

        setMessages(restoredMessages);
        setCurrentSessionMessageCount(restoredMessages.length);

        if (data.latestFeedback) {
          const { messageIndex, rating } = data.latestFeedback;
          setFeedbackMap({
            [messageIndex]: {
              type: rating === 'positive' ? 'up' : 'down',
              disabled: true,
              showConfirm: false
            }
          });
        }

        setHasUserSentMessage(false);

        if (data.customization) {
          if (data.customization.assistantTitle) {
            setAssistantTitle("Ved Ai Assistant");
          }
          if (data.customization.headerColor) {
            setHeaderColor("#495057");
          }
          if (data.customization.primaryColor) {
            // setPrimaryColor(data.customization.primaryColor);
            setPrimaryColor("#495057");
          }
          if (data.customization.fontFamily) {
            const customFont = data.customization.fontFamily;
            const fontWithFallbacks = customFont === 'system-ui'
              ? 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
              : `'${customFont}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
            setFontFamily(fontWithFallbacks);
          }
          if (data.customization.showMinimize !== undefined) {
            setShowMinimize(data.customization.showMinimize);
          }
        }

        setIsOpen(true);
        setIsLoading(false);
        logger.info('Chat opened successfully')
      } else {
        const error = classifyHttpError(response.status);
        console.error(`Session error [${error.code}]:`, response.status);
        setSessionError(error);
        setIsLoading(false);
        setIsOpen(false);
      }

    } catch (error) {
      console.error(`Session fetch error [NETWORK_ERROR]:`, error.message);
      setSessionError(ERROR_TYPES.NETWORK_ERROR);
      setIsLoading(false);
      setIsOpen(false);
    }
  };

  const handleCloseError = () => {
    setSessionError(null);
    setIsOpen(false);
    if (window.parent !== window) {
      window.parent.postMessage({ type: 'CHAT_CLOSED' }, '*');
    }
  };

  // ---------- Chat history (localStorage) ----------
  const loadHistory = () => {
    try {
      if (typeof window === 'undefined' || !window.localStorage) return [];
      const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      logger.warn('History load failed:', e);
      return [];
    }
  };

  const persistHistory = (items) => {
    try {
      if (typeof window === 'undefined' || !window.localStorage) return;
      window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(items.slice(0, MAX_HISTORY_ITEMS)));
    } catch (e) {
      logger.warn('History persist failed:', e);
    }
  };

  // Save the current conversation (skipping the greeting) into history
  const snapshotConversation = () => {
    if (!hasUserSentMessage) return;
    const conversation = messages.filter((_, idx) => idx > 0);
    if (conversation.length === 0) return;

    const firstUser = conversation.find(m => m.role === 'user');
    const title = firstUser ? firstUser.content : 'Conversation';

    const entry = {
      id: `${sessionId || 'sess'}-${Date.now()}`,
      title: title.length > 60 ? title.slice(0, 60) + '…' : title,
      timestamp: Date.now(),
      messages: conversation
    };

    const next = [entry, ...chatHistory.filter(h => h.id !== entry.id)];
    setChatHistory(next);
    persistHistory(next);
  };

  const deleteHistoryItem = (id) => {
    const next = chatHistory.filter(h => h.id !== id);
    setChatHistory(next);
    persistHistory(next);
    if (previewHistoryId === id) setPreviewHistoryId(null);
  };

  const clearAllHistory = () => {
    setChatHistory([]);
    persistHistory([]);
    setPreviewHistoryId(null);
  };

  // Load history on mount
  useEffect(() => {
    setChatHistory(loadHistory());
  }, []);

  // Stop streaming helper - used by stop button and on-typing abort
  const stopResponseGeneration = () => {
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch (e) {
        logger.warn('Abort error:', e);
      }
    }
    setIsStreaming(false);
    setIsThinking(false);
    setStreamingMessage('');
  };

 


 const sendMessageWithStreaming = async (overrideText) => {
  const textToSend = (overrideText !== undefined ? overrideText : inputValue).trim();
  if (!textToSend || isStreaming) return;

  // Add user bubble + clear input
  const newMessages = overrideText !== undefined
    ? [...messages]
    : [...messages, { role: 'user', content: textToSend }];

  if (overrideText === undefined) {
    setMessages(newMessages);
    setInputValue('');
    setCharCount(0);
    if (inputRef.current) inputRef.current.style.height = 'auto';
  }

  // Show typing dots
  setIsStreaming(true);
  setIsThinking(true);
  setStreamingMessage('');
  abortControllerRef.current = new AbortController();

  try {
    // 1. Call FastAPI /api/v1/query
    const res = await fetch('http://localhost:8000/api/v1/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: textToSend,
        k: 5,
        search_type: 'similarity',
        filter: {},
      }),
      signal: abortControllerRef.current.signal,
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const answer = data.answer || 'No response available.';
    const sources = data.sources || [];
    const confidence = data.confidence || 0;
    const confidence_label = data.confidence_label;

    // 2. Switch from "thinking dots" to "streaming text"
    setIsThinking(false);

    // 3. Typewriter effect — render character by character
    let currentText = '';
    const chars = Array.from(answer);          // safer than .split('') for emojis
    const CHAR_DELAY_MS = 12;                  // tweak: lower = faster, higher = slower

    for (let i = 0; i < chars.length; i++) {
      if (abortControllerRef.current?.signal?.aborted) break;
      await new Promise((resolve) => setTimeout(resolve, CHAR_DELAY_MS));
      currentText += chars[i];
      setStreamingMessage(currentText);
    }

    // 4. Commit the final assistant message and clear the streaming bubble
    setMessages([
      ...newMessages,
      { role: 'assistant', content: answer, sources, confidence, confidence_label },
    ]);
    setStreamingMessage('');
  } catch (error) {
    setIsThinking(false);
    setStreamingMessage('');
    if (error?.name !== 'AbortError') {
      setMessages([
        ...newMessages,
        { role: 'assistant', content: 'Something went wrong. Please try again.', isError: true },
      ]);
    }
  } finally {
    setIsStreaming(false);
    setIsThinking(false);
    setStreamingMessage('');
    setReloadingIndex(null);
  }
};



  const handleSend = () => {
    sendMessageWithStreaming()
  };

  const handleClose = () => {
    setShowCloseDialog(true);
  };


  const confirmClose = async () => {
    // Save the conversation to history before tearing it down
    snapshotConversation();

    if (isStreaming && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (sessionId) {
      try {
        const response = await api.deleteSession(sessionId);
        if (response.ok) {
          logger.info('Session closed on backend')
        } else {
          logger.error('Failed to close session:', response.status)
        }
      } catch (error) {
        logger.error('Error closing session:', error)
      }
    }

    setMessages([{ role: 'assistant', content: 'Hi! How can I help you today?' }]);
    setInputValue('');
    setStreamingMessage('');
    setFeedbackMap({});
    setExpandedFeedback(null);
    setFeedbackComment('');
    setCharCount(0);
    setIsThinking(false);
    setIsStreaming(false);
    setIsOpen(false);
    setShowCloseDialog(false);
    setHasUserSentMessage(false);
    setCurrentSessionMessageCount(1);
    setIsMaximized(false);

    if (window.parent !== window) {
      window.parent.postMessage({
        type: 'CHAT_CLOSED',
        sessionId: sessionId
      }, '*');
    }

    setSessionId(null);
    setChatUrl(null);
    logger.info('Session ended, conversation cleared')
  };

  const cancelClose = () => {
    setShowCloseDialog(false);
  };

  const truncate = (str, max = 20) =>
    str.length > max ? str.substring(0, max) + "…" : str;

  const handleThumbsUp = async (messageIndex) => {
    try {
      const response = await api.submitFeedback({
        session_id: sessionId,
        message_index: messageIndex,
        rating: 'positive',
        comment: null,
        message_content: messages[messageIndex].content
      }, sessionId);

      if (response.status === 401 || response.status === 403 || response.status === 404) {
        setSessionError('Session expired or invalid. Please close and try again.');
        setIsOpen(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed');
      }

      setFeedbackMap(prev => ({
        ...prev,
        [messageIndex]: { type: 'up', disabled: true, showConfirm: true }
      }));

      setTimeout(() => {
        setFeedbackMap(prev => ({
          ...prev,
          [messageIndex]: { ...prev[messageIndex], showConfirm: false }
        }));
      }, FEEDBACK_CONFIRM_MS);

    } catch (error) {
      logger.error('Streaming error:', error)
    }
  };

  const handleThumbsDown = (messageIndex) => {
    setExpandedFeedback(messageIndex);
    setFeedbackMap(prev => ({
      ...prev,
      [messageIndex]: { type: 'down', disabled: true }
    }));
  };

  const handleCancelFeedback = (messageIndex) => {
    setExpandedFeedback(null);
    setFeedbackComment('');
    setFeedbackMap(prev => {
      const newMap = { ...prev };
      delete newMap[messageIndex];
      return newMap;
    });
  };

  const handleSubmitFeedback = async (messageIndex) => {
    try {
      const response = await api.submitFeedback({
        session_id: sessionId,
        message_index: messageIndex,
        rating: 'negative',
        comment: feedbackComment,
        message_content: messages[messageIndex].content
      }, sessionId);

      if (response.status === 401 || response.status === 403 || response.status === 404) {
        setSessionError('Session expired or invalid. Please close and try again.');
        setIsOpen(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      setFeedbackMap(prev => ({
        ...prev,
        [messageIndex]: { type: 'down', disabled: true, showConfirm: true }
      }));

      setExpandedFeedback(null);
      setFeedbackComment('');

      setTimeout(() => {
        setFeedbackMap(prev => ({
          ...prev,
          [messageIndex]: { ...prev[messageIndex], showConfirm: false }
        }));
      }, 3000);
    } catch (error) {
      logger.error('Feedback submission error:', error)
    }
  };

  // Copy message content to clipboard
  const handleCopy = async (content, messageIndex) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(content);
      } else {
        // Fallback for older browsers / iframes without clipboard permission
        const ta = document.createElement('textarea');
        ta.value = content;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopiedIndex(messageIndex);
      setTimeout(() => setCopiedIndex(null), 1800);
    } catch (error) {
      logger.error('Copy failed:', error);
    }
  };

  // Reload / regenerate the assistant response for a previous user prompt
  const handleReload = async (messageIndex) => {
    if (isStreaming) return;
    // Find the user message immediately preceding this assistant message
    const userIdx = messageIndex - 1;
    const userMsg = messages[userIdx];
    if (!userMsg || userMsg.role !== 'user') return;

    setReloadingIndex(messageIndex);

    // Trim messages array up to and including the user message
    const trimmed = messages.slice(0, messageIndex);
    setMessages(trimmed);

    // Clear feedback for the regenerated response
    setFeedbackMap(prev => {
      const newMap = { ...prev };
      delete newMap[messageIndex];
      return newMap;
    });

    // Re-send the user prompt without re-appending it
    await sendMessageWithStreaming(userMsg.content);
  };

  const toggleMaximize = () => {
    setIsMaximized(prev => !prev);
  };

  const getPlaceholder = () => {
    return messages.length > 1 ? "Ask a follow-up question..." : "Type your question...";
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleClose();
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim().length >= MIN_INPUT_LENGTH && !isStreaming) {
        handleSend();
      }
    }
  };

  const handleInputChange = (e) => {
    const text = e.target.value.slice(0, MAX_CHARS);

    // Stop response generation if user starts typing while streaming
    if (isStreaming && text.length > 0) {
      stopResponseGeneration();
    }

    setInputValue(text);
    setCharCount(text.length);

    e.target.style.height = 'auto';
    const scrollHeight = e.target.scrollHeight;
    const maxHeight = TEXTAREA_MAX_HEIGHT;
    e.target.style.height = Math.min(scrollHeight, maxHeight) + 'px';
  };

  const toggleSources = (messageIndex) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }));
  };

  // Detect scroll position to show/hide scroll-down arrow
  const handleMessagesScroll = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollDown(distanceFromBottom > 80);
  };

  const isValidSession = chatSessionId &&
    chatSessionId !== null &&
    chatSessionId !== 'null' &&
    typeof chatSessionId === 'string' &&
    chatSessionId.trim().length > 0;

  // Convenience: figure out which assistant messages should show the action row
  const showActionsForIndex = (i, msg) => {
    if (msg.role !== 'assistant' || i === 0) return false;
    if (msg.isError) return false;
    if (feedbackMap[i]) return true;
    return hasUserSentMessage ? i >= currentSessionMessageCount : i === messages.length - 1;
  };

  return (
    <div
      className={`chat-widget${isMaximized && isOpen && !isMinimized ? ' chat-widget-maximized' : ''}`}
      style={{ fontFamily: fontFamily }}
    >
      {!isLoading && isOpen && isValidSession ? (

        <>
          {/* Minimized floating button */}
          {isMinimized ? (
            <button
              className="chat-fab"
              onClick={() => setIsMinimized(false)}
              style={primaryColor ? { backgroundColor: primaryColor } : {}}
              aria-label="Open chat"
            >
              Ask AI
            </button>
          ) : (

            <div
              className={`chat-window${isMaximized ? ' chat-window-maximized' : ''}`}
              style={{ fontFamily: fontFamily }}
            >
              <div className="chat-header" style={headerColor ? { backgroundColor: headerColor } : {}}>
                <div className="chat-header-left">

                  <button
                    className={`chat-hamburger-button${isHistoryOpen ? ' is-active' : ''}`}
                    onClick={() => setIsHistoryOpen(prev => !prev)}
                    aria-label="Toggle chat history"
                    type="button"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="3" y1="6" x2="21" y2="6" />
                      <line x1="3" y1="12" x2="21" y2="12" />
                      <line x1="3" y1="18" x2="21" y2="18" />
                    </svg>
                  </button>

                  <div className="chat-header-content">
                    <Tooltip
                      text={assistantTitle || 'Ask AI Assistant'}
                      backgroundColor={primaryColor || '#000000'}
                      position="bottom"
                    >
                      <h3>
                        {truncate(assistantTitle || 'Ask AI Assistant', TRUNCATE_TITLE)}
                      </h3>
                    </Tooltip>
                  </div>
                </div>
                <div className='widget-action-btn'>

                  {/* Maximize / restore button */}
                  <Tooltip
                    text={isMaximized ? 'Restore' : 'Maximize'}
                    backgroundColor={primaryColor || '#000000'}
                    position="bottom"
                  >
                    <button
                      className="chat-maximize-button"
                      onClick={toggleMaximize}
                      aria-label={isMaximized ? 'Restore chat' : 'Maximize chat'}
                    >
                      {isMaximized ? (
                        // Restore icon (two overlapping rectangles)
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M9 9V5H5v4h4z" />
                          <rect x="9" y="9" width="10" height="10" />
                        </svg>
                      ) : (
                        // Maximize icon (square)
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="4" y="4" width="16" height="16" rx="1" />
                        </svg>
                      )}
                    </button>
                  </Tooltip>

                  {showMinimize && (
                    <button
                      className="chat-minimize-button"
                      onClick={() => setIsMinimized(!isMinimized)}
                      aria-label={isMinimized ? "Expand chat" : "Minimize chat"}
                    >
                      <svg width="24" height="24" viewBox="0 0 24 24">
                        <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2" />
                      </svg>
                    </button>
                  )}

                  {/* Overflow / three-dots menu */}
                  <div className="chat-overflow-wrapper">
                    <Tooltip
                      text={isOverflowOpen ? 'Close menu' : 'More'}
                      backgroundColor={primaryColor || '#000000'}
                      position="bottom"
                    >
                      <button
                        className={`chat-overflow-button${isOverflowOpen ? ' is-active' : ''}`}
                        onClick={() => setIsOverflowOpen(prev => !prev)}
                        aria-label="More options"
                        aria-expanded={isOverflowOpen}
                        type="button"
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                          <circle cx="5" cy="12" r="2" />
                          <circle cx="12" cy="12" r="2" />
                          <circle cx="19" cy="12" r="2" />
                        </svg>
                      </button>
                    </Tooltip>

                    {isOverflowOpen && (
                      <>
                        <div
                          className="chat-overflow-backdrop"
                          onClick={() => setIsOverflowOpen(false)}
                          aria-hidden="true"
                        />
                        <div className="chat-overflow-menu" role="menu">

                          <button className="chat-overflow-item" role="menuitem" type="button" onClick={() => setIsOverflowOpen(false)}>
                            <span className="chat-overflow-icon" aria-hidden="true">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
                              </svg>
                            </span>
                            <span>Feedback</span>
                          </button>
                          <button className="chat-overflow-item" role="menuitem" type="button" onClick={() => setIsOverflowOpen(false)}>
                            <span className="chat-overflow-icon" aria-hidden="true">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                              </svg>
                            </span>
                            <span>Get help</span>
                          </button>
                        </div>
                      </>
                    )}
                  </div>

                  <button
                    className="chat-close-button"
                    onClick={handleClose}
                    aria-label="Close chat"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Sidebar overlay (closes on click) */}
              {isHistoryOpen && (
                <div
                  className="chat-sidebar-overlay"
                  onClick={() => setIsHistoryOpen(false)}
                  aria-hidden="true"
                />
              )}

              {/* Slide-in chat history sidebar */}
              <aside
                className={`chat-sidebar${isHistoryOpen ? ' chat-sidebar-open' : ''}`}
                aria-hidden={!isHistoryOpen}
              >
                <div className="chat-sidebar-header">
                  <span className="chat-sidebar-title">Chat history</span>
                  <button
                    className="chat-sidebar-close"
                    onClick={() => setIsHistoryOpen(false)}
                    aria-label="Close history"
                    type="button"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>

                <div className="chat-sidebar-body">
                  {chatHistory.length === 0 ? (
                    <div className="chat-sidebar-empty">
                      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                      <p>No previous chats yet.</p>
                      <span>Your conversations will appear here.</span>
                    </div>
                  ) : (
                    <ul className="chat-sidebar-list">
                      {chatHistory.map((entry) => {
                        const isCurrent = entry.sessionId === sessionId;
                        const ts = new Date(entry.timestamp);
                        const time = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                        return (
                          <li
                            key={entry.sessionId}
                            className={`chat-sidebar-item${isCurrent ? ' is-current' : ''}`}
                          >
                            <span className="chat-sidebar-item-icon" aria-hidden="true">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                              </svg>
                            </span>
                            <span className="chat-sidebar-item-text">
                              <span className="chat-sidebar-item-title">{entry.title}</span>
                              <span className="chat-sidebar-item-meta">
                                {isCurrent ? 'Current chat • ' : ''}{time}
                              </span>
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              </aside>

              <div
                className="chat-messages"
                ref={messagesContainerRef}
                onScroll={handleMessagesScroll}
                style={{ fontFamily: fontFamily }}
              >

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`message ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}
                  >
                    {msg.role === 'assistant' && (

                      <div className="message-avatar" style={primaryColor ? { backgroundColor: primaryColor } : {}}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </div>
                    )}
                    <div className="message-content">
                      <div className="message-content">
                        <div className="message-bubble">

                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}
                            components={{
                              p: ({ node, ...props }) => <p {...props} />,
                              code: ({ node, inline, ...props }) =>
                                inline ?
                                  <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: '4px' }} {...props} /> :
                                  <code style={{ display: 'block', background: 'rgba(0,0,0,0.1)', padding: '12px', borderRadius: '8px', overflowX: 'auto' }} {...props} />
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {/* Unified action row: thumbs up / thumbs down / sources / copy / reload */}
                        {showActionsForIndex(i, msg) && (
                          <div className="action-row">
                            <Tooltip text="Helpful" backgroundColor={primaryColor || '#000000'}>
                              <button
                                className={`action-btn ${feedbackMap[i]?.type === 'up' ? 'active-up' : ''}`}
                                onClick={() => handleThumbsUp(i)}
                                disabled={feedbackMap[i]?.disabled}
                                aria-label="Helpful"
                              >
                                <svg viewBox="0 0 24 24" width="28" height="28" fill="#495057">
                                  <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57
  .03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 
  8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05
  c.09-.23.14-.47.14-.73v-2z"/>
                                </svg>
                              </button>
                            </Tooltip>

                            <Tooltip text="Not helpful" backgroundColor={primaryColor || '#000000'}>
                              <button
                                className={`action-btn ${feedbackMap[i]?.type === 'down' ? 'active-down' : ''}`}
                                onClick={() => handleThumbsDown(i)}
                                disabled={feedbackMap[i]?.disabled}
                                aria-label="Not helpful"
                              >
                                <svg viewBox="0 0 24 24" width="28" height="28" fill="#495057"
                                  style={{ transform: "rotate(180deg)" }}>
                                  <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57
  .03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 
  8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05
  c.09-.23.14-.47.14-.73v-2z"/>
                                </svg>
                              </button>
                            </Tooltip>

                            {(() => {
                              const hasSources = msg.sources && msg.sources.length > 0;
                              const sourceCount = hasSources
                                ? Math.min([...new Set(msg.sources.map(s => s.source))].length, 3)
                                : 0;
                              return (
                                <Tooltip
                                  text={hasSources ? 'Sources' : 'No sources'}
                                  backgroundColor={primaryColor || '#000000'}
                                >
                                  <button
                                    className={`action-btn ${expandedSources[i] ? 'active-source' : ''}`}
                                    onClick={() => hasSources && toggleSources(i)}
                                    disabled={!hasSources}
                                    aria-label="Toggle sources"
                                  >
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                      <polyline points="14 2 14 8 20 8" />
                                    </svg>
                                    <span className="action-btn-label">{sourceCount}</span>
                                  </button>
                                </Tooltip>
                              );
                            })()}

                            <Tooltip
                              text={copiedIndex === i ? 'Copied!' : 'Copy'}
                              backgroundColor={primaryColor || '#000000'}
                            >
                              <button
                                className={`action-btn ${copiedIndex === i ? 'active-copy' : ''}`}
                                onClick={() => handleCopy(msg.content, i)}
                                aria-label="Copy message"
                              >
                                {copiedIndex === i ? (
                                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12" />
                                  </svg>
                                ) : (
                                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                                  </svg>
                                )}
                              </button>
                            </Tooltip>

                            {/* Only show reload when there's a preceding user message */}
                            {i > 0 && messages[i - 1]?.role === 'user' && (
                              <Tooltip text="Regenerate" backgroundColor={primaryColor || '#000000'}>
                                <button
                                  className={`action-btn ${reloadingIndex === i ? 'active-reload' : ''}`}
                                  onClick={() => handleReload(i)}
                                  disabled={isStreaming}
                                  aria-label="Regenerate response"
                                >
                                  <svg
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    className={reloadingIndex === i ? 'spin' : ''}
                                  >
                                    <polyline points="23 4 23 10 17 10" />
                                    <polyline points="1 20 1 14 7 14" />
                                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                                  </svg>
                                </button>
                              </Tooltip>
                            )}

                            {feedbackMap[i]?.showConfirm && (
                              <span className="feedback-confirm">
                                {feedbackMap[i]?.type === 'up' ? 'Thanks!' : 'Submitted'}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Sources expanded list */}
                        {msg.sources && msg.sources.length > 0 && expandedSources[i] && (
                          <div className="sources-section">
                            <div className="sources-list">
                              {[...new Map(msg.sources.map(s => [s.source, s])).values()].slice(0, 3).map((source, idx) => {
                                const params = new URLSearchParams();
                                params.append('session', sessionId);

                                if (source.page_number) {
                                  params.append('page', source.page_number);
                                }

                                if (source.excerpt) {
                                  params.append('excerpt', source.excerpt);
                                }

                                const s3Key = source.s3_key || source.source;
                                const viewUrl = getViewUrl(s3Key, params);
                                return (
                                  <Tooltip
                                    key={idx}
                                    text={source.source}
                                    backgroundColor={primaryColor || '#000000'}
                                    position="top"
                                  >
                                    <a
                                      href={viewUrl}
                                      className="source-item"
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      <span className="source-icon">📄</span>
                                      <span className="source-name">{source.source}</span>
                                      {source.page_number && (
                                        <>
                                          <span className="source-separator">•</span>
                                          <span className="source-page">Page {source.page_number}</span>
                                        </>
                                      )}
                                      <span className="source-arrow">→</span>
                                    </a>
                                  </Tooltip>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Comment box for thumbs down */}
                        {expandedFeedback === i && (
                          <div className="feedback-comment-box">
                            <textarea
                              placeholder="What went wrong? (500 characters max)"
                              value={feedbackComment}
                              onChange={(e) => setFeedbackComment(e.target.value.slice(0, MAX_FEEDBACK_CHARS))}
                              maxLength={MAX_FEEDBACK_CHARS}
                              rows="3"
                            />
                            <div className="feedback-actions">
                              <button className="cancel-btn" onClick={() => handleCancelFeedback(i)}>
                                Cancel
                              </button>
                              <button
                                className="submit-btn"
                                disabled={!feedbackComment || feedbackComment.trim().length < 3}
                                onClick={() => handleSubmitFeedback(i)}
                              >
                                Submit {feedbackComment.trim().length < 3 && `(${feedbackComment.trim().length}/3)`}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {isStreaming && streamingMessage && (
                  <div className="message message-assistant">
                    <div className="message-avatar" style={primaryColor ? { backgroundColor: primaryColor } : {}} >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div className="message-content">
                      <div className="message-bubble streaming">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}
                          components={{
                            p: ({ node, ...props }) => <p  {...props} />,
                            code: ({ node, inline, ...props }) =>
                              inline ?
                                <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: '4px' }} {...props} /> :
                                <code style={{ display: 'block', background: 'rgba(0,0,0,0.1)', padding: '12px', borderRadius: '8px', overflowX: 'auto' }} {...props} />
                          }}
                        >
                          {streamingMessage}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {isStreaming && !streamingMessage && (
                  <div className="message message-assistant">
                    <div className="message-avatar" style={primaryColor ? { backgroundColor: primaryColor } : {}}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div className="message-content">
                      <div className="message-bubble typing-indicator">
                        <span style={primaryColor ? { backgroundColor: primaryColor } : {}} ></span>
                        <span style={primaryColor ? { backgroundColor: primaryColor } : {}} ></span>
                        <span style={primaryColor ? { backgroundColor: primaryColor } : {}} ></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />

                {showScrollDown && (
                  <button
                    className="scroll-down-btn"
                    onClick={() => scrollToBottom('smooth')}
                    aria-label="Scroll to latest"
                    type="button"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                )}
              </div>

              <div className="chat-input-container" style={{ fontFamily: fontFamily }}>
                <div className="chat-input chat-input-card">
                  <textarea
                    ref={inputRef}
                    placeholder={getPlaceholder()}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    maxLength={MAX_CHARS}
                    className="chat-input-textarea"
                    style={{
                      resize: 'none',
                      overflow: 'auto',
                      overflowX: 'hidden',
                      minHeight: `${TEXTAREA_MIN_HEIGHT}px`,
                      maxHeight: `${TEXTAREA_MAX_HEIGHT}px`,
                      fontFamily: fontFamily
                    }}
                  />
                  <div className="chat-input-toolbar">
                    <div className="chat-input-toolbar-left">
                      <button type="button" className="chat-input-tool-btn" aria-label="Add attachment" tabIndex={-1}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                      </button>
                    </div>
                    <div className="chat-input-toolbar-right">
                      {/* <span className="chat-input-auto" aria-hidden="true">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="16 3 21 3 21 8" />
                          <line x1="4" y1="20" x2="21" y2="3" />
                          <polyline points="21 16 21 21 16 21" />
                          <line x1="15" y1="15" x2="21" y2="21" />
                          <line x1="4" y1="4" x2="9" y2="9" />
                        </svg>
                        <span>Auto</span>
                      </span> */}
                      <button
                        onClick={isStreaming ? stopResponseGeneration : handleSend}
                        disabled={!isStreaming && inputValue.trim().length < 3}
                        className={`send-button ${isStreaming ? 'stop-button' : ''}`}
                        aria-label={isStreaming ? "Stop" : "Send message"}
                        style={!isStreaming && primaryColor ? { backgroundColor: primaryColor } : {}}
                      >
                        {isStreaming ? (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                            <rect x="6" y="6" width="12" height="12" rx="2" />
                          </svg>
                        ) : (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="19" x2="12" y2="5" />
                            <polyline points="5 12 12 5 19 12" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="chat-footer" style={{ fontFamily: fontFamily }}>
                  <span className="ai-disclaimer">
                    <svg className="ai-disclaimer-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="16" x2="12" y2="12" />
                      <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    Uses AI. Verify results.{' '}
                    <a
                      href="/eula.html"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="eula-link"
                      aria-label="Open terms"
                    >
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    </a>
                  </span>
                  <span className="widget-version">Ved Ai {WIDGET_VERSION}</span>
                </div>
                <ConfirmDialog
                  isOpen={showCloseDialog}
                  title="End chat ?"
                  message="When you close this chat, the next session will start as a new conversation. Previous messages won't be shown."
                  primaryButtonText="Close chat"
                  secondaryButtonText="Cancel"
                  primaryColor={primaryColor || '#000000'}
                  onConfirm={confirmClose}
                  onCancel={cancelClose}
                />
              </div>
            </div>
          )}
        </>
      ) : !isLoading && sessionError ? (
        <div className="chat-window" style={{ fontFamily: fontFamily }}>
          <div className="chat-header" style={headerColor ? { backgroundColor: headerColor } : {}}>
            <div className="chat-header-content">
              <Tooltip
                text={'VeD AI Assistant'}
                // text={assistantTitle || 'Ask AI Assistant'}
                backgroundColor={primaryColor || '#000000'}
                position="bottom"
              >
                <h3>
                  {truncate(assistantTitle || 'Ask AI Assistant', 30)}
                </h3>
              </Tooltip>
            </div>
            <button
              className="chat-close-button"
              onClick={handleCloseError}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          <div className="chat-messages" style={{ fontFamily: fontFamily }}>
            <div className="session-error">
              <p>{sessionError?.message || 'Session expired. Please close and try again.'}</p>
              <button
                className="close-btn"
                onClick={handleCloseError}
                style={primaryColor ? { backgroundColor: primaryColor } : {}}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null
      }
    </div>
  );
} 
