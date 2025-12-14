import { motion, AnimatePresence } from 'framer-motion';

export default function TranscriptionOverlay({ text, state }) {
    // Show if text is present or state is listening/thinking
    const isVisible = text || state === 'listening' || state === 'processing';

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 50, opacity: 0 }}
                    className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-3/4 max-w-4xl z-50 pointer-events-none"
                >
                    <div className={`
            p-6 rounded-2xl shadow-2xl backdrop-blur-xl border border-white/10 text-center transition-colors duration-500
            ${state === 'listening' ? 'bg-cyan-900/80' : 'bg-black/70'}
            ${state === 'processing' ? 'border-cyan-400' : ''}
          `}>
                        {state === 'listening' && !text && (
                            <p className="text-cyan-300 font-medium text-xl animate-pulse">Listening...</p>
                        )}

                        {state === 'processing' && (
                            <p className="text-cyan-300 font-medium text-xl animate-pulse">Thinking...</p>
                        )}

                        {text && (
                            <p className="text-white text-2xl font-light leading-relaxed">
                                {text}
                            </p>
                        )}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
