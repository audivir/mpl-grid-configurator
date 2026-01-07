import GridOverlay from "./GridOverlay";
import PreviewOverlay from "./PreviewOverlay";
import { DEFAULT_DPI, RESIZE_DEBOUNCE } from "../lib/const";
import { Layout, FigSize } from "../lib/layout";

interface WorkspaceProps {
  setPresent: (l: Layout, fs: FigSize) => void;
  layout: Layout;
  figsize: FigSize;
  figsizePreview: FigSize;
  showOverlay: boolean;
  svgContent: string;
  zoom: number;
  funcs: string[];
  mergeCallback: (pA: string, pB: string) => void;
}
const Workspace: React.FC<WorkspaceProps> = ({
  setPresent,
  layout,
  figsize,
  figsizePreview,
  showOverlay,
  svgContent,
  zoom,
  funcs,
  mergeCallback,
}) => {
  return (
    <div className="w-full h-full overflow-auto scrollbar-hide">
      <div
        className="relative bg-white shadow-xl origin-top-left transition-transform duration-75 ease-out"
        style={{
          width: `${figsize.w * DEFAULT_DPI}px`,
          height: `${figsize.h * DEFAULT_DPI}px`,
          transform: `scale(${zoom})`,
        }}
      >
        {/* SVG content */}
        <div
          className="absolute inset-0 z-0 pointer-events-none"
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />

        {showOverlay && (
          <div className="absolute inset-0 z-10">
            <GridOverlay
              setPresent={setPresent}
              layout={layout}
              figsize={figsize}
              funcs={funcs}
              zoom={zoom}
              resizeDebounce={RESIZE_DEBOUNCE}
              mergeCallback={mergeCallback}
            />
          </div>
        )}

        {/* Resizing preview */}
        {showOverlay &&
          (figsizePreview.w !== figsize.w ||
            figsizePreview.h !== figsize.h) && ( // During dragging
            <PreviewOverlay figsize={figsizePreview} />
          )}
      </div>
    </div>
  );
};

export default Workspace;
