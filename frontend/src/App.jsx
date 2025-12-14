import { useState, useCallback } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { motion, AnimatePresence } from 'framer-motion';
import Clock from './components/Clock';
import PhotoFrame from './components/PhotoFrame';
import TranscriptionOverlay from './components/TranscriptionOverlay';

export default function App() {
  const [screenIndex, setScreenIndex] = useState(0);
  const screens = ['clock', 'photos'];

  // WebSocket Connection
  // Connect to the Pi's own backend (assuming localhost:8000 if running locally, or relative)
  // For dev, we might need to hardcode or use env.
  // We'll use location.hostname to support both dev and production Pi access.
  const wsUrl = `ws://${window.location.hostname}:8000/api/voice/connect?client_id=frontend_gui`;

  const [transcript, setTranscript] = useState("");
  const [agentState, setAgentState] = useState("idle");

  const { sendMessage, lastJsonMessage, readyState } = useWebSocket(wsUrl, {
    shouldReconnect: (closeEvent) => true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    onOpen: () => console.log('WebSocket Connected'),
    onMessage: (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleWsMessage(msg);
      } catch (e) {
        // console.error(e);
      }
    }
  });

  const handleWsMessage = (msg) => {
    switch (msg.type) {
      case 'set_state':
        setAgentState(msg.data.state.toLowerCase());
        break;
      case 'transcript':
        setTranscript(msg.data.text);
        if (msg.data.is_final) {
          // Optional: clear after delay
          setTimeout(() => setTranscript(""), 5000);
        }
        break;
      case 'session_reset':
        setTranscript("");
        setAgentState("idle");
        break;
      default:
        break;
    }
  };

  // Swipe Logic
  const paginate = (newDirection) => {
    setScreenIndex((prev) => {
      let next = prev + newDirection;
      if (next < 0) next = screens.length - 1;
      if (next >= screens.length) next = 0;
      return next;
    });
  };

  const swipeConfidenceThreshold = 10000;
  const swipePower = (offset, velocity) => {
    return Math.abs(offset) * velocity;
  };

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative">
      <AnimatePresence initial={false} mode="wait">
        <motion.div
          key={screenIndex}
          className="w-full h-full absolute inset-0"
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -300 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={1}
          onDragEnd={(e, { offset, velocity }) => {
            const swipe = swipePower(offset.x, velocity.x);

            if (swipe < -swipeConfidenceThreshold) {
              paginate(1);
            } else if (swipe > swipeConfidenceThreshold) {
              paginate(-1);
            }
          }}
        >
          {screens[screenIndex] === 'clock' && <Clock />}
          {screens[screenIndex] === 'photos' && <PhotoFrame />}
        </motion.div>
      </AnimatePresence>

      <TranscriptionOverlay text={transcript} state={agentState} />

      {/* Connection Indicator (Hidden in prod but useful check) */}
      <div className="fixed top-2 right-2 w-2 h-2 rounded-full z-50 transition-colors"
        style={{ backgroundColor: readyState === ReadyState.OPEN ? '#00ADB5' : '#FF4136' }}
      />
    </div>
  );
}
