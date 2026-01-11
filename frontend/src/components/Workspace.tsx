import GridOverlay from "./GridOverlay";
import PreviewOverlay from "./PreviewOverlay";
import { LayoutActions } from "../lib/actions";
import { DEFAULT_DPI } from "../lib/const";
import { Layout, FigSize } from "../lib/layout";
import { SetStateAction } from "react";

interface WorkspaceProps {
  layout: Layout;
  figsize: FigSize;
  figsizePreview: FigSize;
  showOverlay: boolean;
  svgContent: string;
  setSvgContent: (v: SetStateAction<string>) => void;
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
  setSvgContent,
  zoom,
  funcs,
  actions,
}) => {
  return (
    <div className="w-full h-full overflow-auto scrollbar-hide">
      <div
        className="relative bg-white shadow-xl origin-top-left transition-transform duration-75 ease-out"
        style={{
          width: `${figsize[0] * DEFAULT_DPI}px`,
          height: `${figsize[1] * DEFAULT_DPI}px`,
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
