import GridOverlay from "./GridOverlay";
import PreviewOverlay from "./PreviewOverlay";
import { LayoutActions } from "../lib/actions";
import { DEFAULT_DPI } from "../lib/const";
import { Layout, FigureSize } from "../lib/layout";

interface WorkspaceProps {
  layout: Layout;
  figsize: FigureSize;
  figsizePreview: FigureSize;
  showOverlay: boolean;
  svgContent: string;
  zoom: number;
  funcs: string[];
  actions: LayoutActions;
}
const Workspace: React.FC<WorkspaceProps> = ({
  layout,
  figsize,
  figsizePreview,
  showOverlay,
  svgContent,
  zoom,
  funcs,
  actions,
}) => {
  const [previewWidth, previewHeight] = figsizePreview;
  const pxPreviewWidth = previewWidth * DEFAULT_DPI;
  const pxPreviewHeight = previewHeight * DEFAULT_DPI;
  return (
    <div className="w-full h-full overflow-auto scrollbar-hide">
      <div
        className="relative bg-white shadow-xl origin-top-left transition-transform duration-75 ease-out"
        style={{
          width: `${pxPreviewWidth}px`,
          height: `${pxPreviewHeight}px`,
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
              layout={layout}
              figsize={figsize}
              funcs={funcs}
              zoom={zoom}
              actions={actions}
            />
          </div>
        )}

        {/* Resizing preview */}
        {showOverlay &&
          figsizePreview !== figsize && ( // During dragging
            <PreviewOverlay figsize={figsizePreview} />
          )}
      </div>
    </div>
  );
};

export default Workspace;
