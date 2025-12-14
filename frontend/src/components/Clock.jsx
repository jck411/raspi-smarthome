import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Clock as ClockIcon } from 'lucide-react';

export default function Clock() {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="flex flex-col items-center justify-center h-full w-full bg-black/60 text-white rounded-xl backdrop-blur-md p-10">
            <div className="flex items-center gap-4 mb-4 opacity-70">
                <ClockIcon size={48} />
            </div>
            <div className="text-[12rem] font-bold leading-none tracking-tighter">
                {format(time, 'HH:mm')}
            </div>
            <div className="text-4xl mt-4 font-light text-cyan-400">
                {format(time, 'EEEE, MMMM d')}
            </div>
        </div>
    );
}
