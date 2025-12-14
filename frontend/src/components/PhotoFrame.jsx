import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function PhotoFrame() {
    const [currentImage, setCurrentImage] = useState(0);
    const totalImages = 10;

    // Use picsum for placeholders
    const images = Array.from({ length: totalImages }, (_, i) =>
        `https://picsum.photos/seed/${i + 100}/1920/1080`
    );

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentImage((prev) => (prev + 1) % images.length);
        }, 30000); // Change every 30s
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="w-full h-full relative overflow-hidden bg-black">
            <AnimatePresence mode="wait">
                <motion.img
                    key={currentImage}
                    src={images[currentImage]}
                    alt="Wallpaper"
                    className="absolute inset-0 w-full h-full object-cover"
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5 }}
                />
            </AnimatePresence>
        </div>
    );
}
