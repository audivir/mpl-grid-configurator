/**
 * A full-screen animated spinner with information that Matplotlib is rendering.
 */
const InitialLoader = () => (
  <div className="w-screen h-screen bg-[#0f172a] flex flex-col items-center justify-center gap-6">
    {/* Animated Blueprint/Grid Icon */}
    <div className="relative w-16 h-16 border-2 border-blue-500/30 rounded-lg animate-pulse">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-8 h-[2px] bg-blue-500 rotate-45" />
        <div className="w-8 h-[2px] bg-blue-500 -rotate-45" />
      </div>
      {/* Spinning border */}
      <div className="absolute -inset-2 border-2 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
    </div>

    <div className="text-center">
      <h2 className="text-xl font-bold tracking-widest text-white uppercase">
        Initializing Canvas
      </h2>
      <p className="text-slate-400 text-sm mt-2 font-mono">
        Setting up Matplotlib Session...
      </p>
    </div>
  </div>
);

export default InitialLoader;
