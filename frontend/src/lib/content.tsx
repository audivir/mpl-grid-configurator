/**
 * Copies content to clipboard and sets a temporary success state
 */
export const copyContentToClipboard = async (text: string, setter?: (v: boolean) => void, timeout = 2000) => {
    await navigator.clipboard.writeText(text);
    if (setter) {
        setter(true);
        setTimeout(() => setter(false), timeout);
    }
};

/**
 * Downloads content and sets a temporary success state
 */
export const downloadContent = (content: string, type: string, name: string, setter?: (v: boolean) => void, timeout = 2000) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
    if (setter) {
        setter(true);
        setTimeout(() => setter(false), timeout);
    }
};