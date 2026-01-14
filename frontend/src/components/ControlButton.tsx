import { cn } from "react-lib-tools";

interface ControlButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ElementType;
  label: string;
  variant?: "default" | "danger" | "success";
}

/**
 * A button with an icon and a label.
 */
const ControlButton = ({
  icon: Icon,
  label,
  variant = "default",
  className,
  ...props
}: ControlButtonProps) => {
  const variants = {
    default: "text-slate-400 hover:text-blue-400",
    danger: "text-slate-400 hover:text-red-400",
    success: "text-green-400",
  };

  return (
    <button
      className={cn(
        "flex items-center gap-3 w-full py-2 px-1 transition-colors text-sm font-medium outline-none",
        variants[variant],
        className
      )}
      {...props}
    >
      <Icon size={16} />
      {label}
    </button>
  );
};

export default ControlButton;
